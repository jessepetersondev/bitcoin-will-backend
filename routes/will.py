from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
from models.user import db, User, Will
import json
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ENCRYPTION IMPORTS - ADDED FOR SECURITY
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    ENCRYPTION_AVAILABLE = True
except ImportError:
    print("Cryptography library not available - Bitcoin data will be stored as JSON")
    ENCRYPTION_AVAILABLE = False

will_bp = Blueprint('will', __name__)

# ENCRYPTION FUNCTIONS - ADDED FOR BITCOIN DATA SECURITY
def get_encryption_key():
    """Generate encryption key from environment variable"""
    if not ENCRYPTION_AVAILABLE:
        return None
    
    try:
        # Use environment variable or fallback
        password = os.getenv('BITCOIN_ENCRYPTION_KEY', 'default-bitcoin-will-encryption-key-2024').encode()
        salt = b'bitcoin_will_salt_2024'  # In production, use random salt per user
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    except Exception as e:
        print(f"Encryption key generation error: {e}")
        return None

def encrypt_bitcoin_data(data):
    """Encrypt sensitive Bitcoin data before database storage"""
    if not ENCRYPTION_AVAILABLE or not data:
        return json.dumps(data) if data else '{}'
    
    try:
        key = get_encryption_key()
        if not key:
            return json.dumps(data)
        
        f = Fernet(key)
        json_data = json.dumps(data)
        encrypted_data = f.encrypt(json_data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return json.dumps(data)

def decrypt_bitcoin_data(encrypted_data):
    """Decrypt Bitcoin data for use"""
    if not ENCRYPTION_AVAILABLE or not encrypted_data:
        return {}
    
    try:
        # Try to parse as JSON first (backward compatibility)
        if encrypted_data.startswith('{') or encrypted_data.startswith('['):
            return json.loads(encrypted_data)
        
        key = get_encryption_key()
        if not key:
            return json.loads(encrypted_data)
        
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return json.loads(decrypted_data.decode())
    except Exception as e:
        print(f"Decryption error: {e}")
        try:
            return json.loads(encrypted_data)
        except:
            return {}

def get_user_from_token():
    """Extract user from JWT token - PRESERVED WORKING CODE"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None, jsonify({'message': 'Authorization header missing'}), 401
        
        if not auth_header.startswith('Bearer '):
            return None, jsonify({'message': 'Invalid authorization header format'}), 401
        
        token = auth_header.split(' ')[1]
        
        if not token:
            return None, jsonify({'message': 'Token missing from authorization header'}), 401
        
        # Import JWT functions
        try:
            import jwt
            import os
            JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
            
            # Decode the token manually
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            user_id_str = decoded_token.get('sub')
            
            if not user_id_str:
                return None, jsonify({'message': 'Invalid token payload'}), 401
            
            # Convert string back to integer
            user_id = int(user_id_str)
                
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
    if data is None:
        return default or {}
    
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            print(f"Failed to parse JSON: {data}")
            return default or {}
    
    if isinstance(data, dict):
        return data
    
    return default or {}

def generate_comprehensive_bitcoin_will_pdf(will_data, user_email):
    """Generate comprehensive legal Bitcoin will PDF with ALL original details PLUS legal framework"""
    try:
        print(f"Generating comprehensive Bitcoin will with all details...")
        
        # Parse all JSON fields safely - DECRYPT BITCOIN DATA
        personal_info = safe_json_parse(will_data.get('personal_info'), {})
        assets = decrypt_bitcoin_data(will_data.get('bitcoin_assets')) if will_data.get('bitcoin_assets') else {}
        beneficiaries = decrypt_bitcoin_data(will_data.get('beneficiaries')) if will_data.get('beneficiaries') else {}
        instructions = decrypt_bitcoin_data(will_data.get('executor_instructions')) if will_data.get('executor_instructions') else {}
        
        # Create a BytesIO buffer to hold the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document with legal formatting
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1.25*inch,
            rightMargin=1*inch
        )
        
        # Define comprehensive styles
        styles = getSampleStyleSheet()
        
        # Legal document styles
        title_style = ParagraphStyle(
            'LegalTitle',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        heading_style = ParagraphStyle(
            'LegalHeading',
            parent=styles['Heading2'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.black,
            alignment=TA_CENTER
        )
        
        # Bitcoin data styles (from original)
        bitcoin_heading_style = ParagraphStyle(
            'BitcoinHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        subheading_style = ParagraphStyle(
            'Subheading',
            parent=styles['Heading3'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.black
        )
        
        body_style = ParagraphStyle(
            'LegalBody',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            textColor=colors.black
        )
        
        clause_style = ParagraphStyle(
            'LegalClause',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            spaceAfter=8,
            spaceBefore=4,
            leftIndent=20,
            alignment=TA_JUSTIFY,
            textColor=colors.black
        )
        
        # Build the comprehensive document
        story = []
        
        # LEGAL HEADER
        story.append(Paragraph("LAST WILL AND TESTAMENT", title_style))
        story.append(Paragraph("OF", title_style))
        
        testator_name = personal_info.get('full_name', 'UNKNOWN').upper()
        story.append(Paragraph(testator_name, title_style))
        story.append(Spacer(1, 30))
        
        # LEGAL OPENING DECLARATION
        story.append(Paragraph("ARTICLE I - DECLARATION", heading_style))
        
        address = safe_json_parse(personal_info.get('address'), {})
        city = address.get('city', '[CITY]')
        state = address.get('state', '[STATE]')
        
        opening_text = f"""I, {personal_info.get('full_name', '[NAME]')}, a resident of {city}, {state}, being of sound mind and disposing memory, and not acting under duress, menace, fraud, or undue influence of any person whomsoever, do hereby make, publish, and declare this to be my Last Will and Testament, hereby expressly revoking all former wills and codicils by me at any time heretofore made."""
        
        story.append(Paragraph(opening_text, body_style))
        story.append(Spacer(1, 15))
        
        # REVOCATION CLAUSE
        story.append(Paragraph("ARTICLE II - REVOCATION OF PRIOR WILLS", heading_style))
        story.append(Paragraph("I hereby revoke all wills, codicils, and other testamentary dispositions heretofore made by me. This Will shall supersede and replace any and all prior testamentary documents.", body_style))
        story.append(Spacer(1, 15))
        
        # TESTAMENTARY CAPACITY
        story.append(Paragraph("ARTICLE III - TESTAMENTARY CAPACITY", heading_style))
        story.append(Paragraph("I declare that I am of sound mind and memory, that I have full testamentary capacity, and that I understand the nature and extent of my property and the natural objects of my bounty.", body_style))
        story.append(Spacer(1, 15))
        
        # EXECUTOR APPOINTMENT
        story.append(Paragraph("ARTICLE IV - APPOINTMENT OF EXECUTOR", heading_style))
        
        executor_name = personal_info.get('executor_name', '[EXECUTOR NAME]')
        executor_text = f"""I hereby nominate and appoint {executor_name} as the Executor of this Will. I grant to my Executor comprehensive powers to access, manage, and distribute all digital assets, including Bitcoin and cryptocurrencies, and to engage technical experts as necessary."""
        
        story.append(Paragraph(executor_text, body_style))
        story.append(Spacer(1, 15))
        
        # ===== ORIGINAL BITCOIN WILL CONTENT RESTORED =====
        
        # PERSONAL INFORMATION SECTION (ORIGINAL FORMAT)
        story.append(Paragraph("ARTICLE V - PERSONAL INFORMATION", heading_style))
        
        if personal_info:
            personal_data = [
                ['Full Name:', personal_info.get('full_name', 'N/A')],
                ['Date of Birth:', personal_info.get('date_of_birth', 'N/A')],
                ['Email:', user_email],
                ['Phone:', personal_info.get('phone', 'N/A')],
                ['Executor Name:', personal_info.get('executor_name', 'N/A')],
                ['Executor Contact:', personal_info.get('executor_contact', 'N/A')]
            ]
            
            # Add address details
            if address:
                personal_data.extend([
                    ['Street Address:', address.get('street', 'N/A')],
                    ['City:', address.get('city', 'N/A')],
                    ['State/Province:', address.get('state', 'N/A')],
                    ['ZIP/Postal Code:', address.get('zip_code', 'N/A')],
                    ['Country:', address.get('country', 'N/A')]
                ])
            
            personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
            personal_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(personal_table)
            story.append(Spacer(1, 20))
        
        # BITCOIN ASSETS SECTION (ORIGINAL FORMAT ENHANCED)
        story.append(Paragraph("ARTICLE VI - BITCOIN AND CRYPTOCURRENCY ASSETS", heading_style))
        
        if assets:
            # Digital Wallets (ORIGINAL DETAILED FORMAT)
            wallets = assets.get('wallets', [])
            if wallets and isinstance(wallets, list) and len(wallets) > 0:
                story.append(Paragraph("Digital Wallets:", bitcoin_heading_style))
                
                for i, wallet in enumerate(wallets, 1):
                    wallet_data = safe_json_parse(wallet, {})
                    
                    wallet_info = [
                        [f'Wallet {i}:', ''],
                        ['Wallet Name:', wallet_data.get('name', 'N/A')],
                        ['Type:', wallet_data.get('type', 'N/A')],
                        ['Description:', wallet_data.get('description', 'N/A')],
                        ['Access Method:', wallet_data.get('access_method', 'N/A')],
                        ['Seed Phrase Location:', wallet_data.get('seed_phrase_location', 'N/A')],
                        ['Private Key Location:', wallet_data.get('private_key_location', 'N/A')],
                        ['Additional Notes:', wallet_data.get('additional_notes', 'N/A')]
                    ]
                    
                    wallet_table = Table(wallet_info, colWidths=[1.8*inch, 4.2*inch])
                    wallet_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightblue),
                    ]))
                    
                    story.append(wallet_table)
                    story.append(Spacer(1, 10))
            
            # Exchange Accounts (ORIGINAL DETAILED FORMAT)
            exchanges = assets.get('exchanges', [])
            if exchanges and isinstance(exchanges, list) and len(exchanges) > 0:
                story.append(Paragraph("Exchange Accounts:", bitcoin_heading_style))
                
                for i, exchange in enumerate(exchanges, 1):
                    exchange_data = safe_json_parse(exchange, {})
                    
                    exchange_info = [
                        [f'Exchange {i}:', ''],
                        ['Exchange Name:', exchange_data.get('name', 'N/A')],
                        ['Username/Account ID:', exchange_data.get('username', 'N/A')],
                        ['Email Address:', exchange_data.get('email', 'N/A')],
                        ['2FA Backup Location:', exchange_data.get('two_factor_backup', 'N/A')],
                        ['Additional Notes:', exchange_data.get('additional_notes', 'N/A')]
                    ]
                    
                    exchange_table = Table(exchange_info, colWidths=[1.8*inch, 4.2*inch])
                    exchange_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightyellow),
                    ]))
                    
                    story.append(exchange_table)
                    story.append(Spacer(1, 10))
            
            # Storage Information (ORIGINAL FORMAT)
            if assets.get('storage_method') or assets.get('storage_location') or assets.get('storage_details'):
                story.append(Paragraph("Storage Information:", bitcoin_heading_style))
                
                storage_data = [
                    ['Storage Method:', assets.get('storage_method', 'N/A')],
                    ['Storage Location:', assets.get('storage_location', 'N/A')],
                    ['Storage Details:', assets.get('storage_details', 'N/A')]
                ]
                
                storage_table = Table(storage_data, colWidths=[2*inch, 4*inch])
                storage_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                
                story.append(storage_table)
                story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
        
        # BENEFICIARIES SECTION (ORIGINAL DETAILED FORMAT)
        story.append(Paragraph("ARTICLE VII - BENEFICIARIES AND DISTRIBUTION", heading_style))
        
        if beneficiaries:
            # Primary Beneficiaries (ORIGINAL DETAILED FORMAT)
            primary_beneficiaries = beneficiaries.get('primary', [])
            if primary_beneficiaries and isinstance(primary_beneficiaries, list) and len(primary_beneficiaries) > 0:
                story.append(Paragraph("Primary Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(primary_beneficiaries, 1):
                    beneficiary_data = safe_json_parse(beneficiary, {})
                    
                    beneficiary_info = [
                        [f'Beneficiary {i}:', ''],
                        ['Full Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Email:', beneficiary_data.get('email', 'N/A')],
                        ['Phone:', beneficiary_data.get('phone', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')],
                        ['Additional Notes:', beneficiary_data.get('notes', 'N/A')]
                    ]
                    
                    # Add address if available
                    beneficiary_address = safe_json_parse(beneficiary_data.get('address'), {})
                    if beneficiary_address:
                        beneficiary_info.extend([
                            ['Street Address:', beneficiary_address.get('street', 'N/A')],
                            ['City:', beneficiary_address.get('city', 'N/A')],
                            ['State/Province:', beneficiary_address.get('state', 'N/A')],
                            ['ZIP/Postal Code:', beneficiary_address.get('zip_code', 'N/A')],
                            ['Country:', beneficiary_address.get('country', 'N/A')]
                        ])
                    
                    beneficiary_table = Table(beneficiary_info, colWidths=[1.8*inch, 4.2*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightgreen),
                    ]))
                    
                    story.append(beneficiary_table)
                    story.append(Spacer(1, 10))
            
            # Contingent Beneficiaries (ORIGINAL DETAILED FORMAT)
            contingent_beneficiaries = beneficiaries.get('contingent', [])
            if contingent_beneficiaries and isinstance(contingent_beneficiaries, list) and len(contingent_beneficiaries) > 0:
                story.append(Paragraph("Contingent Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(contingent_beneficiaries, 1):
                    beneficiary_data = safe_json_parse(beneficiary, {})
                    
                    beneficiary_info = [
                        [f'Contingent Beneficiary {i}:', ''],
                        ['Full Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Email:', beneficiary_data.get('email', 'N/A')],
                        ['Phone:', beneficiary_data.get('phone', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')],
                        ['Additional Notes:', beneficiary_data.get('notes', 'N/A')]
                    ]
                    
                    # Add address if available
                    beneficiary_address = safe_json_parse(beneficiary_data.get('address'), {})
                    if beneficiary_address:
                        beneficiary_info.extend([
                            ['Street Address:', beneficiary_address.get('street', 'N/A')],
                            ['City:', beneficiary_address.get('city', 'N/A')],
                            ['State/Province:', beneficiary_address.get('state', 'N/A')],
                            ['ZIP/Postal Code:', beneficiary_address.get('zip_code', 'N/A')],
                            ['Country:', beneficiary_address.get('country', 'N/A')]
                        ])
                    
                    beneficiary_table = Table(beneficiary_info, colWidths=[1.8*inch, 4.2*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightyellow),
                    ]))
                    
                    story.append(beneficiary_table)
                    story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
        
        # EXECUTOR INSTRUCTIONS SECTION (ORIGINAL DETAILED FORMAT)
        story.append(Paragraph("ARTICLE VIII - EXECUTOR INSTRUCTIONS", heading_style))
        
        if instructions:
            # Access Instructions (ORIGINAL FORMAT)
            if instructions.get('access_instructions'):
                story.append(Paragraph("Access Instructions:", bitcoin_heading_style))
                story.append(Paragraph(instructions.get('access_instructions', 'N/A'), body_style))
                story.append(Spacer(1, 10))
            
            # Security Notes (ORIGINAL FORMAT)
            if instructions.get('security_notes'):
                story.append(Paragraph("Security Notes:", bitcoin_heading_style))
                story.append(Paragraph(instructions.get('security_notes', 'N/A'), body_style))
                story.append(Spacer(1, 10))
            
            # Trusted Contacts (ORIGINAL DETAILED FORMAT)
            trusted_contacts = instructions.get('trusted_contacts', [])
            if trusted_contacts and isinstance(trusted_contacts, list) and len(trusted_contacts) > 0:
                story.append(Paragraph("Trusted Contacts:", bitcoin_heading_style))
                
                for i, contact in enumerate(trusted_contacts, 1):
                    contact_data = safe_json_parse(contact, {})
                    
                    contact_info = [
                        [f'Trusted Contact {i}:', ''],
                        ['Name:', contact_data.get('name', 'N/A')],
                        ['Relationship:', contact_data.get('relationship', 'N/A')],
                        ['Email:', contact_data.get('email', 'N/A')],
                        ['Phone:', contact_data.get('phone', 'N/A')],
                        ['Role/Expertise:', contact_data.get('role', 'N/A')],
                        ['Notes:', contact_data.get('notes', 'N/A')]
                    ]
                    
                    contact_table = Table(contact_info, colWidths=[1.8*inch, 4.2*inch])
                    contact_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightcyan),
                    ]))
                    
                    story.append(contact_table)
                    story.append(Spacer(1, 10))
        
        # ===== LEGAL FRAMEWORK CONTINUATION =====
        
        story.append(PageBreak())
        
        # DIGITAL ASSET SPECIFIC PROVISIONS
        story.append(Paragraph("ARTICLE IX - DIGITAL ASSET PROVISIONS", heading_style))
        
        digital_provisions = [
            "I specifically direct my Executor to take all necessary steps to access, secure, and distribute my digital assets, including but not limited to Bitcoin, cryptocurrencies, and other blockchain-based assets.",
            "My Executor is authorized to engage qualified technical experts, including blockchain specialists and cryptocurrency professionals, to assist in the recovery and transfer of digital assets.",
            "I acknowledge that digital assets may be subject to unique technical challenges and authorize my Executor to take reasonable measures to overcome such challenges, including the use of specialized software and hardware.",
            "All costs associated with the recovery and distribution of digital assets shall be paid from my estate as administrative expenses."
        ]
        
        for provision in digital_provisions:
            story.append(Paragraph(provision, clause_style))
        
        story.append(Spacer(1, 15))
        
        # FIDUCIARY POWERS
        story.append(Paragraph("ARTICLE X - FIDUCIARY POWERS", heading_style))
        
        fiduciary_text = """I grant to my Executor the broadest powers permitted by law, including but not limited to the power to: (a) access all digital wallets, exchanges, and storage devices; (b) transfer cryptocurrencies to beneficiaries; (c) liquidate digital assets if necessary; (d) engage professional services; and (e) take any action deemed necessary for the proper administration of my digital estate."""
        
        story.append(Paragraph(fiduciary_text, body_style))
        story.append(Spacer(1, 15))
        
        # TAX CONSIDERATIONS
        story.append(Paragraph("ARTICLE XI - TAX CONSIDERATIONS", heading_style))
        
        tax_text = """I direct my Executor to consider the tax implications of all digital asset transfers and to structure distributions in a manner that minimizes the overall tax burden on my estate and beneficiaries, while complying with all applicable tax laws and regulations."""
        
        story.append(Paragraph(tax_text, body_style))
        story.append(Spacer(1, 15))
        
        # NO CONTEST CLAUSE
        story.append(Paragraph("ARTICLE XII - NO CONTEST CLAUSE", heading_style))
        
        no_contest_text = """If any beneficiary contests this Will or any provision hereof, or seeks to impair or invalidate any provision hereof, then all benefits provided for such beneficiary are revoked and such beneficiary shall receive nothing from my estate."""
        
        story.append(Paragraph(no_contest_text, body_style))
        story.append(Spacer(1, 15))
        
        # SIMULTANEOUS DEATH
        story.append(Paragraph("ARTICLE XIII - SIMULTANEOUS DEATH", heading_style))
        
        simultaneous_death_text = """If any beneficiary and I die under circumstances that make it difficult or impossible to determine who predeceased the other, it shall be presumed that such beneficiary predeceased me."""
        
        story.append(Paragraph(simultaneous_death_text, body_style))
        story.append(Spacer(1, 30))
        
        # EXECUTION SECTION
        story.append(Paragraph("IN WITNESS WHEREOF", heading_style))
        
        execution_text = f"""I have hereunto set my hand this _____ day of _____________, 20___, in the presence of the witnesses whose signatures appear below, each of whom witnessed the signing of this Will at my request and in my presence."""
        
        story.append(Paragraph(execution_text, body_style))
        story.append(Spacer(1, 30))
        
        # Signature lines
        signature_data = [
            ['', ''],
            ['_' * 40, '_' * 40],
            [f'{personal_info.get("full_name", "[TESTATOR NAME]")}', 'Date'],
            ['Testator', ''],
            ['', ''],
            ['WITNESSES:', ''],
            ['', ''],
            ['_' * 40, '_' * 40],
            ['Witness 1 Signature', 'Date'],
            ['', ''],
            ['_' * 40, '_' * 40],
            ['Witness 1 Printed Name', 'Address'],
            ['', ''],
            ['_' * 40, '_' * 40],
            ['Witness 2 Signature', 'Date'],
            ['', ''],
            ['_' * 40, '_' * 40],
            ['Witness 2 Printed Name', 'Address']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # NOTARIZATION SECTION
        story.append(Paragraph("NOTARIZATION", heading_style))
        
        notary_text = """State of _______________
County of _____________

On this _____ day of _____________, 20___, before me personally appeared the above-named Testator and Witnesses, who proved to me on the basis of satisfactory evidence to be the persons whose names are subscribed to the within instrument and acknowledged to me that they executed the same in their authorized capacities.

_________________________________
Notary Public Signature

My commission expires: ___________"""
        
        story.append(Paragraph(notary_text, body_style))
        
        # LEGAL DISCLAIMER
        story.append(PageBreak())
        story.append(Paragraph("IMPORTANT LEGAL NOTICE", heading_style))
        
        disclaimer_text = """This document has been generated using automated legal document software. While it includes standard legal provisions for wills and estate planning, it is strongly recommended that you consult with a qualified attorney licensed in your jurisdiction before executing this document.

Estate planning laws vary by state and country, and individual circumstances may require specific legal provisions not included in this template. This document should be reviewed by legal counsel to ensure compliance with local laws and to address your specific estate planning needs.

The creators of this software disclaim any liability for the legal sufficiency or enforceability of this document. Professional legal advice is recommended for all estate planning matters."""
        
        story.append(Paragraph(disclaimer_text, body_style))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        raise e

@will_bp.route('/list', methods=['GET', 'OPTIONS'])
@cross_origin()
def list_wills():
    """List all wills for the authenticated user - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        wills = Will.query.filter_by(user_id=user.id).all()
        
        will_list = []
        for will in wills:
            # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
            will_dict = {
                'id': will.id,
                'user_id': will.user_id,
                'title': will.title,
                'personal_info': will.personal_info,
                'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
                'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
                'executor_instructions': decrypt_bitcoin_data(will.executor_instructions) if will.executor_instructions else {},
                'status': will.status,
                'created_at': will.created_at.isoformat() if will.created_at else None,
                'updated_at': will.updated_at.isoformat() if will.updated_at else None
            }
            will_list.append(will_dict)
        
        return jsonify({'wills': will_list}), 200
        
    except Exception as e:
        print(f"Error listing wills: {e}")
        return jsonify({'message': 'Failed to retrieve wills'}), 500

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_will():
    """Create a new will - PRESERVED WORKING CODE WITH ENCRYPTION"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Create new will
        will = Will(
            user_id=user.id,
            title=data.get('title', f'Bitcoin Will - {datetime.now().strftime("%Y-%m-%d")}'),
            status='draft'
        )
        
        # Set JSON data - ENCRYPT BITCOIN DATA
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            # ENCRYPT BITCOIN ASSETS BEFORE STORAGE
            encrypted_assets = encrypt_bitcoin_data(data['assets'])
            will.bitcoin_assets = encrypted_assets
        if 'beneficiaries' in data:
            # ENCRYPT BENEFICIARIES BEFORE STORAGE
            encrypted_beneficiaries = encrypt_bitcoin_data(data['beneficiaries'])
            will.beneficiaries = encrypted_beneficiaries
        if 'instructions' in data:
            # ENCRYPT INSTRUCTIONS BEFORE STORAGE
            encrypted_instructions = encrypt_bitcoin_data(data['instructions'])
            will.executor_instructions = encrypted_instructions
        
        db.session.add(will)
        db.session.commit()
        
        # Return will dict with decrypted data for frontend
        # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
        will_dict = {
            'id': will.id,
            'user_id': will.user_id,
            'title': will.title,
            'personal_info': will.personal_info,
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': decrypt_bitcoin_data(will.executor_instructions) if will.executor_instructions else {},
            'status': will.status,
            'created_at': will.created_at.isoformat() if will.created_at else None,
            'updated_at': will.updated_at.isoformat() if will.updated_at else None
        }
        
        return jsonify({
            'message': 'Will created successfully',
            'will': will_dict
        }), 201
        
    except Exception as e:
        print(f"Error creating will: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Failed to create will'}), 500

@will_bp.route('/<int:will_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_will(will_id):
    """Get a specific will - PRESERVED WORKING CODE WITH DECRYPTION"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
        will_dict = {
            'id': will.id,
            'user_id': will.user_id,
            'title': will.title,
            'personal_info': will.personal_info,
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': decrypt_bitcoin_data(will.executor_instructions) if will.executor_instructions else {},
            'status': will.status,
            'created_at': will.created_at.isoformat() if will.created_at else None,
            'updated_at': will.updated_at.isoformat() if will.updated_at else None
        }
        
        return jsonify({'will': will_dict}), 200
        
    except Exception as e:
        print(f"Error retrieving will: {e}")
        return jsonify({'message': 'Failed to retrieve will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def update_will(will_id):
    """Update a will - PRESERVED WORKING CODE WITH ENCRYPTION"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Update will data - ENCRYPT BITCOIN DATA
        if 'title' in data:
            will.title = data['title']
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            # ENCRYPT BITCOIN ASSETS BEFORE STORAGE
            encrypted_assets = encrypt_bitcoin_data(data['assets'])
            will.bitcoin_assets = encrypted_assets
        if 'beneficiaries' in data:
            # ENCRYPT BENEFICIARIES BEFORE STORAGE
            encrypted_beneficiaries = encrypt_bitcoin_data(data['beneficiaries'])
            will.beneficiaries = encrypted_beneficiaries
        if 'instructions' in data:
            # ENCRYPT INSTRUCTIONS BEFORE STORAGE
            encrypted_instructions = encrypt_bitcoin_data(data['instructions'])
            will.executor_instructions = encrypted_instructions
        if 'status' in data:
            will.status = data['status']
        
        will.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Return will dict with decrypted data for frontend
        # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
        will_dict = {
            'id': will.id,
            'user_id': will.user_id,
            'title': will.title,
            'personal_info': will.personal_info,
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': decrypt_bitcoin_data(will.executor_instructions) if will.executor_instructions else {},
            'status': will.status,
            'created_at': will.created_at.isoformat() if will.created_at else None,
            'updated_at': will.updated_at.isoformat() if will.updated_at else None
        }
        
        return jsonify({
            'message': 'Will updated successfully',
            'will': will_dict
        }), 200
        
    except Exception as e:
        print(f"Error updating will: {e}")
        return jsonify({'message': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET', 'OPTIONS'])
@cross_origin()
def download_will(will_id):
    """Download will as PDF - PRESERVED WORKING CODE WITH DECRYPTION"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        print(f"Generating comprehensive Bitcoin will PDF with ALL details for will {will_id}")
        
        # Get will data - DECRYPT FOR PDF GENERATION
        will_data = {
            'personal_info': will.get_personal_info(),
            'bitcoin_assets': will.bitcoin_assets,  # Will be decrypted in PDF function
            'beneficiaries': will.beneficiaries,    # Will be decrypted in PDF function
            'executor_instructions': will.executor_instructions  # Will be decrypted in PDF function
        }
        
        print(f"Will data structure: {will_data}")
        
        # Generate comprehensive Bitcoin will PDF with ALL original details + legal framework
        pdf_data = generate_comprehensive_bitcoin_will_pdf(will_data, user.email)
        
        # Create a BytesIO object from the PDF data
        pdf_buffer = io.BytesIO(pdf_data)
        pdf_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_will_{will_id}_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error generating will PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Failed to generate PDF'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_will(will_id):
    """Delete a will - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code
    
    try:
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting will: {e}")
        return jsonify({'message': 'Failed to delete will'}), 500

