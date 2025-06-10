from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

will_bp = Blueprint('will', __name__)

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_will():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        return jsonify({
            'message': 'Will created successfully',
            'will': {
                'id': 1,
                'title': data.get('title', 'My Bitcoin Will'),
                'created_at': '2024-01-01T00:00:00'
            }
        }), 201

    except Exception as e:
        print(f"Create will error: {e}")
        return jsonify({'error': 'Failed to create will'}), 500

@will_bp.route('/list', methods=['GET'])
@cross_origin()
def list_wills():
    try:
        return jsonify({
            'wills': []
        }), 200

    except Exception as e:
        print(f"List wills error: {e}")
        return jsonify({'error': 'Failed to list wills'}), 500

@will_bp.route('/<int:will_id>', methods=['GET'])
@cross_origin()
def get_will(will_id):
    try:
        return jsonify({
            'will': {
                'id': will_id,
                'title': 'Sample Will',
                'created_at': '2024-01-01T00:00:00'
            }
        }), 200

    except Exception as e:
        print(f"Get will error: {e}")
        return jsonify({'error': 'Failed to get will'}), 500

