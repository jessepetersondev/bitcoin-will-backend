from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models.user import db, User
import stripe
import os
import re

auth_bp = Blueprint('auth', __name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY') 

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Valid password"

def get_user_from_token():
    """Extract user from JWT token with better error handling"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None, jsonify({'message': 'Authorization header missing'}), 401
        
        if not auth_header.startswith('Bearer '):
            return None, jsonify({'message': 'Invalid authorization header format'}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return None, jsonify({'message': 'Token missing from authorization header'}), 401
        
        # Try to decode the token
        try:
            from flask_jwt_extended import decode_token
            decoded_token = decode_token(token)
            user_id = decoded_token.get('sub')
            
            if not user_id:
                return None, jsonify({'message': 'Invalid token payload'}), 401
                
        except Exception as jwt_error:
            print(f"JWT decode error: {jwt_error}")
            # Try alternative approach - use get_jwt_identity with current_app context
            try:
                from flask import current_app
                from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
                
                with current_app.test_request_context():
                    # Set the authorization header in the test context
                    current_app.test_request_context().request.headers = {'Authorization': auth_header}
                    verify_jwt_in_request()
                    user_id = get_jwt_identity()
                    
            except Exception as alt_error:
                print(f"Alternative JWT verification failed: {alt_error}")
                return None, jsonify({'message': 'Invalid or expired token'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return None, jsonify({'message': 'User not found'}), 404
            
        return user, None, None
        
    except Exception as e:
        print(f"Token validation error: {e}")
        return None, jsonify({'message': 'Authentication failed'}), 401

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin()
def register():
    if request.method == 'OPTIONS':
        # This handles the preflight request
        return '', 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validate required fields
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 422

        # Validate email format
        if not validate_email(email):
            return jsonify({'message': 'Invalid email format'}), 422

        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'message': message}), 422

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 422

        # Create user without stripe_customer_id for now
        user = User(email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Create Stripe customer after user is created (optional)
        stripe_customer_id = None
        try:
            if stripe.api_key and stripe.api_key.startswith('sk_'):
                stripe_customer = stripe.Customer.create(
                    email=email,
                    metadata={
                        'user_id': str(user.id),
                        'source': 'bitcoin_will_app'
                    }
                )
                stripe_customer_id = stripe_customer.id
                print(f"Created Stripe customer: {stripe_customer_id} for user {user.id}")
        except Exception as stripe_error:
            print(f"Stripe customer creation failed (non-critical): {stripe_error}")

        # Create access token with longer expiration
        access_token = create_access_token(identity=user.id, expires_delta=False)

        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({'message': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validate required fields
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 422

        # Find user
        user = User.query.filter_by(email=email).first()

        # Check credentials
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid email or password'}), 401

        # Create access token with longer expiration
        access_token = create_access_token(identity=user.id, expires_delta=False)

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': 'Login failed. Please try again.'}), 500

@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin()
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404

        return jsonify({'user': user.to_dict()}), 200

    except Exception as e:
        print(f"Get current user error: {e}")
        return jsonify({'message': 'Failed to get user information'}), 500

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@cross_origin()
def logout():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # In a stateless JWT system, logout is handled client-side
        # by removing the token from storage
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'message': 'Logout failed'}), 500

