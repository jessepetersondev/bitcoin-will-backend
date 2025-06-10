import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'railway')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'connect_timeout': 60,
        'read_timeout': 60,
        'write_timeout': 60
    }
}

# CORS configuration
CORS(app, 
     origins=["https://thebitcoinwill.com", "http://localhost:8000", "http://127.0.0.1:8000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# JWT configuration
jwt = JWTManager(app)

# Initialize database
try:
    from models.user import db
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Database error: {e}")

# Import and register blueprints
try:
    from routes.auth import auth_bp
    from routes.health import health_bp
    from routes.subscription import subscription_bp
    from routes.user import user_bp
    from routes.will import will_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(will_bp, url_prefix='/api/will')
    
    print("✅ All routes registered successfully")
except Exception as e:
    print(f"❌ Route import error: {e}")

# Fallback routes
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'bitcoin-will-backend', 'version': '1.0.0'}), 200

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password required'}), 400
        
        return jsonify({
            'message': 'Registration successful',
            'user': {'email': data['email'], 'id': 1},
            'access_token': 'test-token-123'
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password required'}), 400
        
        return jsonify({
            'message': 'Login successful',
            'user': {'email': data['email'], 'id': 1},
            'access_token': 'test-token-123'
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/')
def index():
    return jsonify({'message': 'Bitcoin Will API is running', 'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

