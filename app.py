import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# CORS configuration
CORS(app, 
     origins=["https://thebitcoinwill.com", "http://localhost:8000", "http://127.0.0.1:8000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True )

# JWT configuration
jwt = JWTManager(app)

# Health check route
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'bitcoin-will-backend', 'version': '1.0.0'}), 200

@app.route('/')
def index():
    return jsonify({'message': 'Bitcoin Will API is running', 'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
