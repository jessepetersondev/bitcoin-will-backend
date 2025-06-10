from flask import Blueprint, request, jsonify
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
    """Extract user from JWT token - WITH DEBUG LOGGING"""
    try:
        auth_header = request.headers.get('Authorization')
        print(f"DEBUG: Authorization header: {auth_header}")
        
        if not auth_header:
            print("DEBUG: No authorization header")
            return None, jsonify({'message': 'Authorization header missing'}), 401
        
        if not auth_header.startswith('Bearer '):
            print("DEBUG: Invalid authorization header format")
            return None, jsonify({'message': 'Invalid authorization header format'}), 401
        
        token = auth_header.split(' ')[1]
        print(f"DEBUG: Extracted token: {token[:50]}...")
        
        if not token:
            print("DEBUG: Token missing from authorization header")
            return None, jsonify({'message': 'Token missing from authorization header'}), 401
        
        # Import JWT functions
        try:
            import jwt
            JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
            print(f"DEBUG: JWT Secret Key: {JWT_SECRET_KEY}")
            
            # Decode the token manually
            print("DEBUG: Attempting to decode token...")
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            print(f"DEBUG: Decoded token: {decoded_token}")
            
            user_id = decoded_token.get('sub')
            print(f"DEBUG: User ID from token: {user_id}")
            
            if not user_id:
                print("DEBUG: Invalid token payload - no user ID")
                return None, jsonify({'message': 'Invalid token payload'}), 401
                
        except jwt.ExpiredSignatureError:
            print("DEBUG: Token has expired")
            return None, jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            print(f"DEBUG: JWT decode error: {e}")
            return None, jsonify({'message': 'Invalid token'}), 401
        except Exception as jwt_error:
            print(f"DEBUG: JWT processing error: {jwt_error}")
            return None, jsonify({'message': 'Token validation failed'}), 401
        
        user = User.query.get(user_id)
        print(f"DEBUG: Found user: {user.email if user else 'None'}")
        
        if not user:
            print("DEBUG: User not found in database")
            return None, jsonify({'message': 'User not found'}), 404
            
        return user, None, None
        
    except Exception as e:
        print(f"DEBUG: Token validation error: {e}")
        return None, jsonify({'message': 'Authentication failed'}), 401

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin()
def register():
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

        # Create user
        user = User(email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Create access token manually
        import jwt
        from datetime import datetime, timedelta
        
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
        print(f"DEBUG: Creating token with secret: {JWT_SECRET_KEY}")
        
        payload = {
            'sub': user.id,
            'email': user.email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30)  # 30 day expiration
        }
        
        print(f"DEBUG: Token payload: {payload}")
        
        access_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        print(f"DEBUG: Created token: {access_token[:50]}...")

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

        # Create access token manually
        import jwt
        from datetime import datetime, timedelta
        
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
        print(f"DEBUG: Creating login token with secret: {JWT_SECRET_KEY}")
        
        payload = {
            'sub': user.id,
            'email': user.email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30)  # 30 day expiration
        }
        
        print(f"DEBUG: Login token payload: {payload}")
        
        access_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        print(f"DEBUG: Created login token: {access_token[:50]}...")

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': 'Login failed. Please try again.'}), 500

@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        print("DEBUG: /auth/me endpoint called")
        user, error_response, status_code = get_user_from_token()
        if not user:
            print(f"DEBUG: Authentication failed with status {status_code}")
            return error_response, status_code

        print(f"DEBUG: Authentication successful for user {user.email}")
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
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'message': 'Logout failed'}), 500

# Debug endpoint to check JWT configuration
@auth_bp.route('/debug-jwt', methods=['GET'])
@cross_origin()
def debug_jwt():
    """Debug endpoint to check JWT configuration"""
    try:
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
        
        # Create a test token
        import jwt
        from datetime import datetime, timedelta
        
        test_payload = {
            'sub': 999,
            'email': 'test@example.com',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=5)
        }
        
        test_token = jwt.encode(test_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        # Try to decode it
        decoded = jwt.decode(test_token, JWT_SECRET_KEY, algorithms=['HS256'])
        
        return jsonify({
            'jwt_secret_configured': bool(os.getenv('JWT_SECRET_KEY')),
            'jwt_secret_value': JWT_SECRET_KEY,
            'test_token_created': True,
            'test_token_decoded': True,
            'decoded_payload': decoded
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'jwt_secret_configured': bool(os.getenv('JWT_SECRET_KEY')),
            'jwt_secret_value': os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
        }), 500

