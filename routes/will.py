from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Will, Subscription
from src.services.will_generator import WillGenerator
import os

will_bp = Blueprint('will', __name__)

@will_bp.route('/create', methods=['POST'])
@jwt_required()
def create_will():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user has active subscription
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()

        if not subscription:
            return jsonify({'error': 'Active subscription required'}), 403

        data = request.get_json()
        
        # Create new will
        will = Will(
            user_id=user_id,
            title=data.get('title', 'My Bitcoin Will')
        )
        
        # Set will data
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'bitcoin_assets' in data:
            will.set_bitcoin_assets(data['bitcoin_assets'])
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
        return jsonify({'error': str(e)}), 500

@will_bp.route('/list', methods=['GET'])
@jwt_required()
def list_wills():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        wills = Will.query.filter_by(user_id=user_id).order_by(Will.created_at.desc()).all()
        
        return jsonify({
            'wills': [will.to_dict() for will in wills]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@will_bp.route('/<int:will_id>', methods=['GET'])
@jwt_required()
def get_will(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404

        return jsonify({'will': will.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@will_bp.route('/<int:will_id>', methods=['PUT'])
@jwt_required()
def update_will(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404

        data = request.get_json()
        
        # Update will data
        if 'title' in data:
            will.title = data['title']
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'bitcoin_assets' in data:
            will.set_bitcoin_assets(data['bitcoin_assets'])
        if 'beneficiaries' in data:
            will.set_beneficiaries(data['beneficiaries'])
        if 'instructions' in data:
            will.set_instructions(data['instructions'])

        db.session.commit()

        return jsonify({
            'message': 'Will updated successfully',
            'will': will.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@will_bp.route('/<int:will_id>/generate', methods=['POST'])
@jwt_required()
def generate_will_document(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404

        # Check if user has active subscription
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()

        if not subscription:
            return jsonify({'error': 'Active subscription required'}), 403

        # Generate PDF document
        generator = WillGenerator()
        pdf_path = generator.generate_will_pdf(will)
        
        # Update will with document path
        will.document_path = pdf_path
        db.session.commit()

        return jsonify({
            'message': 'Will document generated successfully',
            'document_path': pdf_path
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET'])
@jwt_required()
def download_will_document(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404

        if not will.document_path or not os.path.exists(will.document_path):
            return jsonify({'error': 'Document not found. Please generate the document first.'}), 404

        return send_file(
            will.document_path,
            as_attachment=True,
            download_name=f"{will.title.replace(' ', '_')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE'])
@jwt_required()
def delete_will(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404

        # Delete document file if exists
        if will.document_path and os.path.exists(will.document_path):
            os.remove(will.document_path)

        db.session.delete(will)
        db.session.commit()

        return jsonify({'message': 'Will deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

