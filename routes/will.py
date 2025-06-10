from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models.user import db, User, Will
from services.will_generator import WillGenerator
import json
from datetime import datetime

will_bp = Blueprint('will', __name__)

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def create_will():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
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
        print(f"Create will error: {e}")
        return jsonify({'error': 'Failed to create will'}), 500

@will_bp.route('/list', methods=['GET'])
@cross_origin()
@jwt_required()
def list_wills():
    try:
        user_id = get_jwt_identity()
        wills = Will.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'wills': [will.to_dict() for will in wills]
        }), 200

    except Exception as e:
        print(f"List wills error: {e}")
        return jsonify({'error': 'Failed to list wills'}), 500

@will_bp.route('/<int:will_id>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_will(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404
            
        return jsonify({'will': will.to_dict()}), 200

    except Exception as e:
        print(f"Get will error: {e}")
        return jsonify({'error': 'Failed to get will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
@jwt_required()
def update_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
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
            
        will.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Will updated successfully',
            'will': will.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Update will error: {e}")
        return jsonify({'error': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>/generate', methods=['POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def generate_will_document(will_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404
            
        # Generate PDF document
        generator = WillGenerator()
        document_path = generator.generate_will_pdf(will)
        
        # Update will with document path
        will.document_path = document_path
        db.session.commit()
        
        return jsonify({
            'message': 'Will document generated successfully',
            'document_path': document_path,
            'download_url': f'/api/will/{will_id}/download'
        }), 200

    except Exception as e:
        print(f"Generate will error: {e}")
        return jsonify({'error': 'Failed to generate will document'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET'])
@cross_origin()
@jwt_required()
def download_will(will_id):
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will or not will.document_path:
            return jsonify({'error': 'Will document not found'}), 404
            
        from flask import send_file
        return send_file(will.document_path, as_attachment=True, download_name=f'bitcoin_will_{will_id}.pdf')

    except Exception as e:
        print(f"Download will error: {e}")
        return jsonify({'error': 'Failed to download will'}), 500

@will_bp.route('/template', methods=['GET'])
@cross_origin()
@jwt_required()
def get_will_template():
    """Get the will creation template with all required fields"""
    try:
        template = {
            'personal_info': {
                'full_name': '',
                'date_of_birth': '',
                'address': {
                    'street': '',
                    'city': '',
                    'state': '',
                    'zip_code': '',
                    'country': ''
                },
                'phone': '',
                'email': '',
                'social_security': ''
            },
            'bitcoin_assets': {
                'wallets': [
                    {
                        'name': '',
                        'type': 'hardware|software|paper|exchange',
                        'description': '',
                        'access_method': '',
                        'seed_phrase_location': '',
                        'private_key_location': '',
                        'additional_notes': ''
                    }
                ],
                'exchanges': [
                    {
                        'name': '',
                        'username': '',
                        'email': '',
                        'two_factor_backup': '',
                        'additional_notes': ''
                    }
                ],
                'other_crypto': [
                    {
                        'currency': '',
                        'amount': '',
                        'location': '',
                        'access_method': ''
                    }
                ]
            },
            'beneficiaries': [
                {
                    'name': '',
                    'relationship': '',
                    'percentage': 0,
                    'address': {
                        'street': '',
                        'city': '',
                        'state': '',
                        'zip_code': '',
                        'country': ''
                    },
                    'phone': '',
                    'email': '',
                    'bitcoin_address': '',
                    'backup_contact': {
                        'name': '',
                        'phone': '',
                        'email': ''
                    }
                }
            ],
            'instructions': {
                'executor': {
                    'name': '',
                    'relationship': '',
                    'phone': '',
                    'email': '',
                    'address': {
                        'street': '',
                        'city': '',
                        'state': '',
                        'zip_code': '',
                        'country': ''
                    }
                },
                'distribution_instructions': '',
                'technical_instructions': '',
                'emergency_contacts': [
                    {
                        'name': '',
                        'relationship': '',
                        'phone': '',
                        'email': ''
                    }
                ],
                'additional_notes': '',
                'lawyer_contact': {
                    'name': '',
                    'firm': '',
                    'phone': '',
                    'email': '',
                    'address': ''
                }
            }
        }
        
        return jsonify({'template': template}), 200

    except Exception as e:
        print(f"Get template error: {e}")
        return jsonify({'error': 'Failed to get template'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
@jwt_required()
def delete_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        will = Will.query.filter_by(id=will_id, user_id=user_id).first()
        
        if not will:
            return jsonify({'error': 'Will not found'}), 404
            
        # Delete document file if exists
        if will.document_path:
            import os
            try:
                os.remove(will.document_path)
            except:
                pass
                
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Delete will error: {e}")
        return jsonify({'error': 'Failed to delete will'}), 500

