from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models.user import db, User, Will
import json
from datetime import datetime

will_bp = Blueprint('will', __name__)

@will_bp.route('/list', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin()
def list_wills():
    """Get user's wills"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        wills = Will.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'wills': [will.to_dict() for will in wills]
        }), 200
        
    except Exception as e:
        print(f"List wills error: {e}")
        return jsonify({'message': 'Failed to get wills'}), 500

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def create_will():
    """Create a new will"""
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
        
        # Create new will
        will = Will(
            user_id=user_id,
            title=data.get('title', 'My Bitcoin Will'),
            status='draft'
        )
        
        # Set JSON data
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            will.set_bitcoin_assets(data['assets'])
        if 'beneficiaries' in data:
            will.set_beneficiaries(data['beneficiaries'])
        if 'instructions' in data:
            will.set_instructions(data['instructions'])
        
        db.session.add(will)
        db.session.commit()
        
        return jsonify({
            'message': 'Will created successfully',
            'will': will.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create will error: {e}")
        return jsonify({'message': 'Failed to create will'}), 500

@will_bp.route('/<int:will_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin()
def get_will(will_id):
    """Get a specific will"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        return jsonify({'will': will.to_dict()}), 200
        
    except Exception as e:
        print(f"Get will error: {e}")
        return jsonify({'message': 'Failed to get will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
@cross_origin()
def update_will(will_id):
    """Update a will"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
        
        # Update will data
        if 'title' in data:
            will.title = data['title']
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            will.set_bitcoin_assets(data['assets'])
        if 'beneficiaries' in data:
            will.set_beneficiaries(data['beneficiaries'])
        if 'instructions' in data:
            will.set_instructions(data['instructions'])
        if 'status' in data:
            will.status = data['status']
        
        will.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Will updated successfully',
            'will': will.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update will error: {e}")
        return jsonify({'message': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin()
def download_will(will_id):
    """Download will as PDF"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # For now, return a placeholder response
        # In production, you would generate and return the actual PDF
        return jsonify({
            'message': 'PDF generation not implemented yet',
            'will_id': will_id
        }), 200
        
    except Exception as e:
        print(f"Download will error: {e}")
        return jsonify({'message': 'Failed to download will'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
@cross_origin()
def delete_will(will_id):
    """Delete a will"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete will error: {e}")
        return jsonify({'message': 'Failed to delete will'}), 500

