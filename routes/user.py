from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@jwt_required()
@cross_origin()
def get_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'message': 'Failed to retrieve users'}), 500

@user_bp.route('/users', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_user():
    """Create a new user"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 422
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 422
            
        user = User(email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create user error: {e}")
        return jsonify({'message': 'Failed to create user'}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def get_user(user_id):
    """Get a specific user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Users can only access their own data unless admin
        if current_user_id != user_id:
            return jsonify({'message': 'Access denied'}), 403
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'message': 'Failed to retrieve user'}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
@cross_origin()
def update_user(user_id):
    """Update a user"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        current_user_id = get_jwt_identity()
        
        # Users can only update their own data
        if current_user_id != user_id:
            return jsonify({'message': 'Access denied'}), 403
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        # Update allowed fields
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=email).filter(User.id != user_id).first()
            if existing_user:
                return jsonify({'message': 'Email already taken'}), 422
            user.email = email
            
        if 'password' in data:
            password = data['password']
            if len(password) < 6:
                return jsonify({'message': 'Password must be at least 6 characters long'}), 422
            user.set_password(password)
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update user error: {e}")
        return jsonify({'message': 'Failed to update user'}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
@cross_origin()
def delete_user(user_id):
    """Delete a user"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        current_user_id = get_jwt_identity()
        
        # Users can only delete their own account
        if current_user_id != user_id:
            return jsonify({'message': 'Access denied'}), 403
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete user error: {e}")
        return jsonify({'message': 'Failed to delete user'}), 500

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@cross_origin()
def get_user_profile():
    """Get current user's profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({'message': 'Failed to get user profile'}), 500

@user_bp.route('/profile', methods=['PUT', 'OPTIONS'])
@jwt_required()
@cross_origin()
def update_user_profile():
    """Update current user's profile"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        # Update allowed fields
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken
            existing_user = User.query.filter_by(email=email).filter(User.id != user_id).first()
            if existing_user:
                return jsonify({'message': 'Email already taken'}), 422
            user.email = email
            
        if 'password' in data:
            password = data['password']
            if len(password) < 6:
                return jsonify({'message': 'Password must be at least 6 characters long'}), 422
            user.set_password(password)
        
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update profile error: {e}")
        return jsonify({'message': 'Failed to update profile'}), 500

