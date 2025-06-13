from flask import Blueprint, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import jwt
from datetime import datetime, timedelta
from functools import wraps
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io
import os
import base64

# SECURITY: Import encryption modules
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets

# Initialize blueprint
will_bp = Blueprint('will', __name__)

# SECURITY: Encryption class for Bitcoin data
class BitcoinDataEncryption:
    def __init__(self, password=None):
        """Initialize encryption with a password or generate one"""
        if password is None:
            # Use environment variable or generate a secure key
            password = os.environ.get('BITCOIN_ENCRYPTION_KEY', self._generate_key())
        
        self.password = password.encode() if isinstance(password, str) else password
        self._fernet = None
    
    def _generate_key(self):
        """Generate a secure encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _get_fernet(self):
        """Get or create Fernet instance"""
        if self._fernet is None:
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'bitcoin_will_salt_2024',  # In production, use random salt per user
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.password))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if not data:
            return data
        
        try:
            # Convert to JSON string if it's a dict
            if isinstance(data, dict):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            
            # Encrypt the data
            encrypted = self._get_fernet().encrypt(data_str.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return data  # Return original data if encryption fails
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._get_fernet().decrypt(encrypted_bytes)
            decrypted_str = decrypted.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data  # Return original data if decryption fails

# Initialize encryption
bitcoin_encryption = BitcoinDataEncryption()

# SECURITY: Enhanced logging
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger('bitcoin_will_security')

def log_security_event(event_type, user_id, details):
    """Log security events"""
    security_logger.info(f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}")

def get_user_from_token():
    """Extract user from JWT token - COMPATIBLE WITH EXISTING AUTH"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None, jsonify({'message': 'Authorization header missing'}), 401
        
        if not auth_header.startswith('Bearer '):
            return None, jsonify({'message': 'Invalid authorization header format'}), 401
        
        token = auth_header.split(' ')[1]
        
        if not token:
            return None, jsonify({'message': 'Token missing from authorization header'}), 401
        
        # Import User model here to avoid circular imports
        from models.user import User
        
        # Import JWT functions
        try:
            import jwt
            import os
            JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
            
            # Decode the token manually - COMPATIBLE WITH EXISTING TOKENS
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            user_id_str = decoded_token.get('sub')
            
            if not user_id_str:
                return None, jsonify({'message': 'Invalid token payload'}), 401
            
            # Convert string back to integer
            user_id = int(user_id_str)
            
            # SECURITY: Log access attempt
            log_security_event('API_ACCESS', user_id, f"Endpoint: {request.endpoint}")
                
        except jwt.ExpiredSignatureError:
            return None, jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            print(f"JWT decode error: {e}")
            return None, jsonify({'message': 'Invalid token'}), 401
        except ValueError:
            return None, jsonify({'message': 'Invalid user ID in token'}), 401
        except Exception as jwt_error:
            print(f"JWT processing error: {jwt_error}")
            return None, jsonify({'message': 'Token validation failed'}), 401
        
        user = User.query.get(user_id)
        
        if not user:
            return None, jsonify({'message': 'User not found'}), 404
            
        return user, None, None
        
    except Exception as e:
        print(f"Token validation error: {e}")
        return None, jsonify({'message': 'Authentication failed'}), 401

def safe_json_parse(data, default=None):
    """Safely parse JSON data that might be a string or already parsed"""
    if default is None:
        default = {}
    
    if data is None:
        return default
    
    if isinstance(data, dict):
        return data
    
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parse error: {e}")
            return default
    
    return default

@will_bp.route('/create', methods=['POST'])
def create_will():
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # SECURITY: Log will creation attempt
        log_security_event('WILL_CREATE_ATTEMPT', user.id, "Creating new will")
        
        # SECURITY: Encrypt sensitive Bitcoin data before storing
        encrypted_assets = bitcoin_encryption.encrypt_data(data.get('assets', {}))
        encrypted_beneficiaries = bitcoin_encryption.encrypt_data(data.get('beneficiaries', {}))
        encrypted_instructions = bitcoin_encryption.encrypt_data(data.get('instructions', {}))
        
        # Personal info can remain unencrypted (or encrypt if preferred)
        personal_info = data.get('personal_info', {})
        
        # Import here to avoid circular imports
        from models.user import Will, db
        
        will = Will(
            user_id=user.id,
            title=data.get('title', f'Bitcoin Will - {datetime.now().strftime("%Y-%m-%d")}'),
            personal_info=json.dumps(personal_info),
            assets=encrypted_assets,  # ENCRYPTED
            beneficiaries=encrypted_beneficiaries,  # ENCRYPTED
            instructions=encrypted_instructions,  # ENCRYPTED
            status='draft'
        )
        
        db.session.add(will)
        db.session.commit()
        
        # SECURITY: Log successful creation
        log_security_event('WILL_CREATED', user.id, f"Will ID: {will.id}")
        
        return jsonify({
            'message': 'Will created successfully',
            'will_id': will.id
        }), 201
        
    except Exception as e:
        print(f"Will creation error: {e}")
        # SECURITY: Log error without sensitive details
        log_security_event('WILL_CREATE_ERROR', user.id if 'user' in locals() else 'UNKNOWN', "Will creation failed")
        return jsonify({'message': 'Failed to create will'}), 500

@will_bp.route('/list', methods=['GET'])
def list_wills():
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        from models.user import Will
        
        wills = Will.query.filter_by(user_id=user.id).all()
        
        will_list = []
        for will in wills:
            will_list.append({
                'id': will.id,
                'title': will.title,
                'status': will.status,
                'created_at': will.created_at.isoformat(),
                'updated_at': will.updated_at.isoformat(),
                'testator_name': safe_json_parse(will.personal_info).get('full_name', 'Unknown')
            })
        
        return jsonify(will_list), 200
        
    except Exception as e:
        print(f"Will list error: {e}")
        return jsonify({'message': 'Failed to retrieve wills'}), 500

@will_bp.route('/<int:will_id>', methods=['GET'])
def get_will(will_id):
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        from models.user import Will
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # SECURITY: Decrypt sensitive data for authorized user
        decrypted_assets = bitcoin_encryption.decrypt_data(will.assets)
        decrypted_beneficiaries = bitcoin_encryption.decrypt_data(will.beneficiaries)
        decrypted_instructions = bitcoin_encryption.decrypt_data(will.instructions)
        
        # SECURITY: Log data access
        log_security_event('WILL_ACCESSED', user.id, f"Will ID: {will_id}")
        
        return jsonify({
            'id': will.id,
            'title': will.title,
            'personal_info': safe_json_parse(will.personal_info),
            'assets': decrypted_assets,
            'beneficiaries': decrypted_beneficiaries,
            'instructions': decrypted_instructions,
            'status': will.status,
            'created_at': will.created_at.isoformat(),
            'updated_at': will.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Will retrieval error: {e}")
        return jsonify({'message': 'Failed to retrieve will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT'])
def update_will(will_id):
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        from models.user import Will, db
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # SECURITY: Log update attempt
        log_security_event('WILL_UPDATE_ATTEMPT', user.id, f"Will ID: {will_id}")
        
        # SECURITY: Encrypt sensitive data before updating
        if 'assets' in data:
            will.assets = bitcoin_encryption.encrypt_data(data['assets'])
        if 'beneficiaries' in data:
            will.beneficiaries = bitcoin_encryption.encrypt_data(data['beneficiaries'])
        if 'instructions' in data:
            will.instructions = bitcoin_encryption.encrypt_data(data['instructions'])
        
        # Update non-sensitive data
        if 'title' in data:
            will.title = data['title']
        if 'personal_info' in data:
            will.personal_info = json.dumps(data['personal_info'])
        if 'status' in data:
            will.status = data['status']
        
        will.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # SECURITY: Log successful update
        log_security_event('WILL_UPDATED', user.id, f"Will ID: {will_id}")
        
        return jsonify({'message': 'Will updated successfully'}), 200
        
    except Exception as e:
        print(f"Will update error: {e}")
        log_security_event('WILL_UPDATE_ERROR', user.id if 'user' in locals() else 'UNKNOWN', f"Will ID: {will_id}")
        return jsonify({'message': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE'])
def delete_will(will_id):
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        from models.user import Will, db
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # SECURITY: Log deletion attempt
        log_security_event('WILL_DELETE_ATTEMPT', user.id, f"Will ID: {will_id}")
        
        db.session.delete(will)
        db.session.commit()
        
        # SECURITY: Log successful deletion
        log_security_event('WILL_DELETED', user.id, f"Will ID: {will_id}")
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        print(f"Will deletion error: {e}")
        return jsonify({'message': 'Failed to delete will'}), 500

def generate_comprehensive_legal_pdf(will_data, user_email):
    """Generate a comprehensive legal Bitcoin will PDF with all user data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles for legal document
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Times-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Times-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Times-Roman'
    )
    
    # Build document content
    content = []
    
    # Document title
    content.append(Paragraph("LAST WILL AND TESTAMENT", title_style))
    content.append(Paragraph("FOR BITCOIN AND DIGITAL ASSETS", title_style))
    content.append(Spacer(1, 20))
    
    # Personal information
    personal_info = safe_json_parse(will_data.get('personal_info', {}))
    testator_name = personal_info.get('full_name', 'Unknown')
    
    content.append(Paragraph("ARTICLE I - DECLARATION", heading_style))
    content.append(Paragraph(f"I, {testator_name}, being of sound mind and disposing memory, do hereby make, publish, and declare this to be my Last Will and Testament for my Bitcoin and digital assets, hereby revoking all former wills and codicils made by me.", body_style))
    content.append(Spacer(1, 12))
    
    # Personal Information Table
    if personal_info:
        content.append(Paragraph("TESTATOR INFORMATION", heading_style))
        
        personal_data = [
            ['Full Name:', personal_info.get('full_name', 'Not specified')],
            ['Date of Birth:', personal_info.get('date_of_birth', 'Not specified')],
            ['Phone:', personal_info.get('phone', 'Not specified')],
            ['Email:', user_email],
        ]
        
        # Add address if available
        address = personal_info.get('address', {})
        if address and any(address.values()):
            full_address = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}, {address.get('country', '')}"
            personal_data.append(['Address:', full_address.strip(', ')])
        
        personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        content.append(personal_table)
        content.append(Spacer(1, 20))
    
    # Bitcoin Assets Section
    assets = will_data.get('assets', {})
    if assets:
        content.append(Paragraph("ARTICLE II - BITCOIN AND DIGITAL ASSETS", heading_style))
        content.append(Paragraph("I hereby declare and bequeath the following Bitcoin and digital assets:", body_style))
        content.append(Spacer(1, 12))
        
        # Storage Information
        if assets.get('storage_method') or assets.get('storage_location'):
            content.append(Paragraph("STORAGE INFORMATION", heading_style))
            storage_data = [
                ['Storage Method:', assets.get('storage_method', 'Not specified')],
                ['Storage Location:', assets.get('storage_location', 'Not specified')],
                ['Storage Details:', assets.get('storage_details', 'Not specified')],
            ]
            
            storage_table = Table(storage_data, colWidths=[2*inch, 4*inch])
            storage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            content.append(storage_table)
            content.append(Spacer(1, 15))
        
        # Wallets
        wallets = assets.get('wallets', [])
        if wallets:
            content.append(Paragraph("BITCOIN WALLETS", heading_style))
            for i, wallet in enumerate(wallets, 1):
                if wallet and any(wallet.values()):
                    content.append(Paragraph(f"Wallet {i}:", ParagraphStyle('WalletHeader', parent=body_style, fontName='Times-Bold')))
                    
                    wallet_data = [
                        ['Name/Label:', wallet.get('name', 'Not specified')],
                        ['Type:', wallet.get('type', 'Not specified')],
                        ['Description:', wallet.get('description', 'Not specified')],
                        ['Access Method:', wallet.get('access_method', 'Not specified')],
                        ['Seed Phrase Location:', wallet.get('seed_phrase_location', 'Not specified')],
                        ['Private Key Location:', wallet.get('private_key_location', 'Not specified')],
                        ['Additional Notes:', wallet.get('additional_notes', 'Not specified')],
                    ]
                    
                    wallet_table = Table(wallet_data, colWidths=[2*inch, 4*inch])
                    wallet_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    content.append(wallet_table)
                    content.append(Spacer(1, 10))
        
        # Exchanges
        exchanges = assets.get('exchanges', [])
        if exchanges:
            content.append(Paragraph("EXCHANGE ACCOUNTS", heading_style))
            for i, exchange in enumerate(exchanges, 1):
                if exchange and any(exchange.values()):
                    content.append(Paragraph(f"Exchange {i}:", ParagraphStyle('ExchangeHeader', parent=body_style, fontName='Times-Bold')))
                    
                    exchange_data = [
                        ['Exchange Name:', exchange.get('name', 'Not specified')],
                        ['Username/Account ID:', exchange.get('username', 'Not specified')],
                        ['Email Address:', exchange.get('email', 'Not specified')],
                        ['2FA Backup Codes:', exchange.get('two_factor_backup', 'Not specified')],
                        ['Additional Notes:', exchange.get('additional_notes', 'Not specified')],
                    ]
                    
                    exchange_table = Table(exchange_data, colWidths=[2*inch, 4*inch])
                    exchange_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    content.append(exchange_table)
                    content.append(Spacer(1, 10))
    
    # Beneficiaries Section
    beneficiaries = will_data.get('beneficiaries', {})
    if beneficiaries:
        content.append(Paragraph("ARTICLE III - BENEFICIARIES", heading_style))
        
        # Primary Beneficiaries
        primary = beneficiaries.get('primary', [])
        if primary:
            content.append(Paragraph("PRIMARY BENEFICIARIES", heading_style))
            for i, beneficiary in enumerate(primary, 1):
                if beneficiary and any(beneficiary.values()):
                    content.append(Paragraph(f"Primary Beneficiary {i}:", ParagraphStyle('BeneficiaryHeader', parent=body_style, fontName='Times-Bold')))
                    
                    beneficiary_data = [
                        ['Name:', beneficiary.get('name', 'Not specified')],
                        ['Relationship:', beneficiary.get('relationship', 'Not specified')],
                        ['Percentage:', f"{beneficiary.get('percentage', '0')}%"],
                        ['Phone:', beneficiary.get('phone', 'Not specified')],
                        ['Email:', beneficiary.get('email', 'Not specified')],
                        ['Bitcoin Address:', beneficiary.get('bitcoin_address', 'Not specified')],
                    ]
                    
                    # Add address if available
                    address = beneficiary.get('address', {})
                    if address and any(address.values()):
                        full_address = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}, {address.get('country', '')}"
                        beneficiary_data.append(['Address:', full_address.strip(', ')])
                    
                    beneficiary_table = Table(beneficiary_data, colWidths=[2*inch, 4*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    content.append(beneficiary_table)
                    content.append(Spacer(1, 10))
        
        # Contingent Beneficiaries
        contingent = beneficiaries.get('contingent', [])
        if contingent:
            content.append(Paragraph("CONTINGENT BENEFICIARIES", heading_style))
            for i, beneficiary in enumerate(contingent, 1):
                if beneficiary and any(beneficiary.values()):
                    content.append(Paragraph(f"Contingent Beneficiary {i}:", ParagraphStyle('ContingentHeader', parent=body_style, fontName='Times-Bold')))
                    
                    beneficiary_data = [
                        ['Name:', beneficiary.get('name', 'Not specified')],
                        ['Relationship:', beneficiary.get('relationship', 'Not specified')],
                        ['Percentage:', f"{beneficiary.get('percentage', '0')}%"],
                        ['Phone:', beneficiary.get('phone', 'Not specified')],
                        ['Email:', beneficiary.get('email', 'Not specified')],
                        ['Bitcoin Address:', beneficiary.get('bitcoin_address', 'Not specified')],
                    ]
                    
                    # Add address if available
                    address = beneficiary.get('address', {})
                    if address and any(address.values()):
                        full_address = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}, {address.get('country', '')}"
                        beneficiary_data.append(['Address:', full_address.strip(', ')])
                    
                    beneficiary_table = Table(beneficiary_data, colWidths=[2*inch, 4*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightsteelblue),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    content.append(beneficiary_table)
                    content.append(Spacer(1, 10))
    
    # Instructions Section
    instructions = will_data.get('instructions', {})
    if instructions:
        content.append(Paragraph("ARTICLE IV - EXECUTOR INSTRUCTIONS", heading_style))
        
        if instructions.get('access_instructions'):
            content.append(Paragraph("ACCESS INSTRUCTIONS", ParagraphStyle('InstructionHeader', parent=body_style, fontName='Times-Bold')))
            content.append(Paragraph(instructions.get('access_instructions', ''), body_style))
            content.append(Spacer(1, 10))
        
        if instructions.get('security_notes'):
            content.append(Paragraph("SECURITY NOTES", ParagraphStyle('SecurityHeader', parent=body_style, fontName='Times-Bold')))
            content.append(Paragraph(instructions.get('security_notes', ''), body_style))
            content.append(Spacer(1, 10))
        
        if instructions.get('additional_instructions'):
            content.append(Paragraph("ADDITIONAL INSTRUCTIONS", ParagraphStyle('AdditionalHeader', parent=body_style, fontName='Times-Bold')))
            content.append(Paragraph(instructions.get('additional_instructions', ''), body_style))
            content.append(Spacer(1, 10))
        
        if instructions.get('emergency_contact'):
            content.append(Paragraph("EMERGENCY CONTACT", ParagraphStyle('EmergencyHeader', parent=body_style, fontName='Times-Bold')))
            content.append(Paragraph(instructions.get('emergency_contact', ''), body_style))
            content.append(Spacer(1, 10))
        
        # Trusted Contacts
        trusted_contacts = instructions.get('trusted_contacts', [])
        if trusted_contacts:
            content.append(Paragraph("TRUSTED CONTACTS", ParagraphStyle('TrustedHeader', parent=body_style, fontName='Times-Bold')))
            for i, contact in enumerate(trusted_contacts, 1):
                if contact and any(contact.values()):
                    contact_data = [
                        ['Name:', contact.get('name', 'Not specified')],
                        ['Contact Info:', contact.get('contact', 'Not specified')],
                        ['Relationship:', contact.get('relationship', 'Not specified')],
                        ['Role/Expertise:', contact.get('role', 'Not specified')],
                    ]
                    
                    contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
                    contact_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgoldenrodyellow),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    content.append(contact_table)
                    content.append(Spacer(1, 8))
    
    # Executor Information
    if personal_info.get('executor_name'):
        content.append(Paragraph("ARTICLE V - EXECUTOR", heading_style))
        executor_data = [
            ['Executor Name:', personal_info.get('executor_name', 'Not specified')],
            ['Executor Contact:', personal_info.get('executor_contact', 'Not specified')],
        ]
        
        executor_table = Table(executor_data, colWidths=[2*inch, 4*inch])
        executor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        content.append(executor_table)
        content.append(Spacer(1, 20))
    
    # Legal clauses
    content.append(Paragraph("ARTICLE VI - LEGAL PROVISIONS", heading_style))
    
    legal_clauses = [
        "This will is executed with the intent to comply with applicable laws regarding digital asset inheritance.",
        "I direct my executor to work with qualified legal and technical professionals to ensure proper transfer of digital assets.",
        "All Bitcoin and digital assets shall be distributed according to the percentages specified for each beneficiary.",
        "In the event that any beneficiary predeceases me, their share shall be distributed among the remaining beneficiaries proportionally.",
        "This will supplements but does not replace my primary will for physical assets and other property.",
    ]
    
    for clause in legal_clauses:
        content.append(Paragraph(f"• {clause}", body_style))
        content.append(Spacer(1, 6))
    
    # Signature section
    content.append(Spacer(1, 30))
    content.append(Paragraph("ARTICLE VII - EXECUTION", heading_style))
    content.append(Paragraph("IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of _____________, 20___.", body_style))
    content.append(Spacer(1, 30))
    
    # Signature lines
    signature_data = [
        ['', ''],
        ['_' * 40, '_' * 40],
        [f'{testator_name}', 'Date'],
        ['Testator', ''],
        ['', ''],
        ['WITNESSES:', ''],
        ['', ''],
        ['_' * 40, '_' * 40],
        ['Witness 1 Signature', 'Date'],
        ['', ''],
        ['_' * 40, '_' * 40],
        ['Witness 2 Signature', 'Date'],
    ]
    
    signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    content.append(signature_table)
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer

@will_bp.route('/<int:will_id>/download', methods=['GET'])
def download_will(will_id):
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        from models.user import Will
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # SECURITY: Log download attempt
        log_security_event('WILL_DOWNLOAD', user.id, f"Will ID: {will_id}")
        
        print(f"Generating comprehensive legal PDF for will {will_id}")
        
        # SECURITY: Decrypt data for PDF generation
        decrypted_assets = bitcoin_encryption.decrypt_data(will.assets)
        decrypted_beneficiaries = bitcoin_encryption.decrypt_data(will.beneficiaries)
        decrypted_instructions = bitcoin_encryption.decrypt_data(will.instructions)
        
        will_data = {
            'personal_info': safe_json_parse(will.personal_info),
            'assets': decrypted_assets,
            'beneficiaries': decrypted_beneficiaries,
            'instructions': decrypted_instructions
        }
        
        pdf_buffer = generate_comprehensive_legal_pdf(will_data, user.email)
        
        # SECURITY: Log successful download
        log_security_event('WILL_DOWNLOADED', user.id, f"Will ID: {will_id}")
        
        from flask import Response
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=bitcoin_will_{will_id}.pdf'}
        )
        
    except Exception as e:
        print(f"Legal PDF generation error: {e}")
        log_security_event('WILL_DOWNLOAD_ERROR', user.id if 'user' in locals() else 'UNKNOWN', f"Will ID: {will_id}")
        return jsonify({'message': 'Failed to generate will PDF'}), 500

