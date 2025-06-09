from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    wills = db.relationship('Will', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'stripe_customer_id': self.stripe_customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # active, canceled, past_due, etc.
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Will(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    personal_info = db.Column(db.Text, nullable=True)  # JSON string
    bitcoin_assets = db.Column(db.Text, nullable=True)  # JSON string
    beneficiaries = db.Column(db.Text, nullable=True)  # JSON string
    instructions = db.Column(db.Text, nullable=True)  # JSON string
    document_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_personal_info(self, data):
        self.personal_info = json.dumps(data)

    def get_personal_info(self):
        return json.loads(self.personal_info) if self.personal_info else {}

    def set_bitcoin_assets(self, data):
        self.bitcoin_assets = json.dumps(data)

    def get_bitcoin_assets(self):
        return json.loads(self.bitcoin_assets) if self.bitcoin_assets else {}

    def set_beneficiaries(self, data):
        self.beneficiaries = json.dumps(data)

    def get_beneficiaries(self):
        return json.loads(self.beneficiaries) if self.beneficiaries else {}

    def set_instructions(self, data):
        self.instructions = json.dumps(data)

    def get_instructions(self):
        return json.loads(self.instructions) if self.instructions else {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'personal_info': self.get_personal_info(),
            'bitcoin_assets': self.get_bitcoin_assets(),
            'beneficiaries': self.get_beneficiaries(),
            'instructions': self.get_instructions(),
            'document_path': self.document_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

