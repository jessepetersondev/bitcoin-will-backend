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

        # Create Stripe customer (optional, don't fail if Stripe is not configured)
        stripe_customer_id = None
        try:
            if stripe.api_key and stripe.api_key.startswith('sk_'):
                stripe_customer = stripe.Customer.create(
                    email=email,
                    metadata={'source': 'bitcoin_will_app'}
                )
                stripe_customer_id = stripe_customer.id
        except Exception as stripe_error:
            print(f"Stripe customer creation failed (non-critical): {stripe_error}")

        # Create user
        user = User(
            email=email, 
            stripe_customer_id=stripe_customer_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=user.id)

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

        # Create access token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': 'Login failed. Please try again.'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
@cross_origin()
def get_current_user():
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
@jwt_required()
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

