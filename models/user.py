from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    wills = db.relationship('Will', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # 'monthly' or 'yearly'
    status = db.Column(db.String(50), nullable=False, default='active')  # 'active', 'cancelled', 'expired'
    stripe_subscription_id = db.Column(db.String(255))
    btcpay_invoice_id = db.Column(db.String(255))
    payment_method = db.Column(db.String(50), nullable=False)  # 'stripe' or 'btcpay'
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'status': self.status,
            'payment_method': self.payment_method,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Will(db.Model):
    __tablename__ = 'wills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False, default='My Bitcoin Will')
    personal_info = db.Column(db.Text)  # JSON string
    bitcoin_assets = db.Column(db.Text)  # JSON string
    beneficiaries = db.Column(db.Text)  # JSON string
    instructions = db.Column(db.Text)  # JSON string
    document_path = db.Column(db.String(500))  # Path to generated PDF
    status = db.Column(db.String(50), nullable=False, default='draft')  # 'draft', 'completed', 'archived'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_personal_info(self, data):
        """Set personal info as encrypted JSON string"""
        from will import encrypt_bitcoin_data
        self.personal_info = encrypt_bitcoin_data(data) if data else None
    
    def get_personal_info(self):
        """Get personal info as Python dict"""
        from will import decrypt_bitcoin_data
        if not self.personal_info:
            return {}
        try:
            return decrypt_bitcoin_data(self.personal_info)
        except Exception as e:
            print(f"Error decrypting personal info: {e}")
            # Fallback to JSON parsing for backward compatibility
            try:
                return json.loads(self.personal_info) if self.personal_info else {}
            except:
                return {}
    
    def set_bitcoin_assets(self, data):
        """Set bitcoin assets as JSON string"""
        self.bitcoin_assets = json.dumps(data) if data else None
    
    def get_bitcoin_assets(self):
        """Get bitcoin assets as Python dict"""
        return json.loads(self.bitcoin_assets) if self.bitcoin_assets else {}
    
    def set_beneficiaries(self, data):
        """Set beneficiaries as JSON string"""
        self.beneficiaries = json.dumps(data) if data else None
    
    def get_beneficiaries(self):
        """Get beneficiaries as Python list"""
        return json.loads(self.beneficiaries) if self.beneficiaries else []
    
    def set_instructions(self, data):
        """Set instructions as JSON string"""
        self.instructions = json.dumps(data) if data else None
    
    def get_instructions(self):
        """Get instructions as Python dict"""
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
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

