from flask import Blueprint, jsonify
from flask_cors import cross_origin
from models.user import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for Railway"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'bitcoin-will-backend',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@health_bp.route('/ready', methods=['GET'])
@cross_origin()
def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'ready',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@health_bp.route('/ping', methods=['GET'])
@cross_origin()
def ping():
    """Simple ping endpoint"""
    try:
        return jsonify({
            'message': 'pong',
            'timestamp': db.func.now()
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'pong',
            'error': str(e)
        }), 200

