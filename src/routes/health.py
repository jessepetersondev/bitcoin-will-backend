from flask import Blueprint, jsonify
from src.models.user import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'bitcoin-will-backend',
        'version': '1.0.0'
    }), 200

@health_bp.route('/ready', methods=['GET'])
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
            'error': str(e)
        }), 503

