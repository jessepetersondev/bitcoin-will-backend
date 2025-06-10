from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@cross_origin()
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    user = User(email=data['email'])
    if 'password' in data:
        user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@cross_origin()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def update_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    user = User.query.get_or_404(user_id)
    data = request.json
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

