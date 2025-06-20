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

def safe_decrypt_bitcoin_data(encrypted_data):
    """Safely decrypt Bitcoin data with enhanced error handling"""
    if not encrypted_data:
        return {}
    
    try:
        return decrypt_bitcoin_data(encrypted_data)
    except Exception as e:
        print(f"Decryption error: {e}")
        # Try to parse as JSON (fallback for non-encrypted data)
        try:
            if isinstance(encrypted_data, str):
                return json.loads(encrypted_data)
            return encrypted_data if isinstance(encrypted_data, dict) else {}
        except:
            return {}

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
    
    # Handle unexpected data types (like integers)
    if isinstance(data, (int, float, bool)):
        print(f"Warning: Expected dict/string but got {type(data)}: {data}")
        return default or {}
    
    return default or {}

def generate_comprehensive_bitcoin_will_pdf(will_data, user_email):
    """Generate Bitcoin Asset Addendum PDF - A supplementary document for existing wills"""
    try:
        print(f"Generating Bitcoin Asset Addendum document...")
        
        # Parse all JSON fields safely - DECRYPT BITCOIN DATA
        personal_info = safe_json_parse(will_data.get('personal_info'), {})
        assets = decrypt_bitcoin_data(will_data.get('bitcoin_assets')) if will_data.get('bitcoin_assets') else {}
        beneficiaries = decrypt_bitcoin_data(will_data.get('beneficiaries')) if will_data.get('beneficiaries') else {}
        instructions = decrypt_bitcoin_data(will_data.get('executor_instructions')) if will_data.get('executor_instructions') else {}
        legal_compliance = decrypt_bitcoin_data(will_data.get('legal_compliance')) if will_data.get('legal_compliance') else {}
        
        # Extract document title for PDF metadata
        document_title = "Bitcoin Asset Addendum"
        if will_data.get('title'):
            document_title = f"{will_data.get('title')} - Bitcoin Asset Addendum"
        elif personal_info.get('title'):
            document_title = f"{personal_info.get('title')} - Bitcoin Asset Addendum"
        elif personal_info.get('fullName') or personal_info.get('full_name'):
            full_name = personal_info.get('fullName') or personal_info.get('full_name')
            document_title = f"{full_name} - Bitcoin Asset Addendum"
        
        # Create a BytesIO buffer to hold the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document with legal formatting AND METADATA
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1.25*inch,
            rightMargin=1*inch,
            title=document_title,  # SET PDF TITLE METADATA
            author="TheBitcoinWill.com",  # SET PDF AUTHOR METADATA
            subject="Bitcoin Asset Addendum to Last Will and Testament",  # SET PDF SUBJECT
            creator="TheBitcoinWill.com - Bitcoin Estate Planning Service"  # SET PDF CREATOR
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
        
        # ADDENDUM HEADER
        story.append(Paragraph("BITCOIN ASSET ADDENDUM", title_style))
        story.append(Paragraph("TO LAST WILL AND TESTAMENT", title_style))
        story.append(Paragraph("OF", title_style))
        
        testator_name = personal_info.get('full_name', 'UNKNOWN').upper()
        story.append(Paragraph(testator_name, title_style))
        story.append(Spacer(1, 30))
        
        # ADDENDUM DECLARATION
        story.append(Paragraph("ARTICLE I - ADDENDUM DECLARATION", heading_style))
        
        # SAFE ADDRESS PARSING - Handle any data type
        address_data = personal_info.get('address', {})
        address = safe_json_parse(address_data, {})
        
        # Ensure address is a dictionary before calling .get()
        if not isinstance(address, dict):
            print(f"Warning: Address data is not a dict: {type(address)} = {address}")
            address = {}
        
        city = address.get('city', '[CITY]') if isinstance(address, dict) else '[CITY]'
        state = address.get('state', '[STATE]') if isinstance(address, dict) else '[STATE]'
        
        opening_text = f"""I, {personal_info.get('full_name', '[NAME]')}, a resident of {city}, {state}, being of sound mind and disposing memory, do hereby make, publish, and declare this Bitcoin Asset Addendum to be a supplement to my existing Last Will and Testament. This addendum specifically addresses the disposition of my Bitcoin assets and shall be incorporated into and become part of my Last Will and Testament."""
        
        story.append(Paragraph(opening_text, body_style))
        story.append(Spacer(1, 15))
        
        # ADDENDUM SCOPE
        story.append(Paragraph("ARTICLE II - SCOPE OF ADDENDUM", heading_style))
        story.append(Paragraph("This addendum supplements but does not replace my existing Last Will and Testament. It specifically covers Bitcoin assets and related Bitcoin property. In the event of any conflict between this addendum and my primary will regarding Bitcoin assets, this addendum shall control.", body_style))
        story.append(Spacer(1, 15))
        
        # BITCOIN ASSET ACKNOWLEDGMENT
        story.append(Paragraph("ARTICLE III - BITCOIN ASSET ACKNOWLEDGMENT", heading_style))
        story.append(Paragraph("I acknowledge that I own or may own Bitcoin assets. I understand the unique nature of Bitcoin and the importance of proper access instructions for my beneficiaries and executor.", body_style))
        story.append(Spacer(1, 15))
        
        # EXECUTOR POWERS FOR BITCOIN ASSETS
        story.append(Paragraph("ARTICLE IV - EXECUTOR POWERS FOR BITCOIN ASSETS", heading_style))
        
        executor_name = personal_info.get('executor_name', '[EXECUTOR NAME]')
        executor_text = f"""I grant to my Executor, {executor_name}, and any successor executor, comprehensive powers to access, manage, and distribute all Bitcoin assets described in this addendum. This includes the authority to engage technical experts, Bitcoin specialists, and other professionals as necessary to properly handle these Bitcoin assets."""
        
        story.append(Paragraph(executor_text, body_style))
        story.append(Spacer(1, 15))
        
        # ===== BITCOIN ASSET INVENTORY =====
        
        # BITCOIN ASSET INVENTORY SECTION
        story.append(Paragraph("ARTICLE V - BITCOIN ASSET INVENTORY", heading_style))
        
        # Add basic identification for addendum reference
        story.append(Paragraph("Testator Identification:", body_style))
        if personal_info:
            identification_data = [
                ['Full Legal Name:', personal_info.get('full_name', 'N/A')],
                ['Date of Birth:', personal_info.get('date_of_birth', 'N/A')],
                ['Executor Name:', personal_info.get('executor_name', 'N/A')],
                ['Executor Contact:', personal_info.get('executor_contact', 'N/A')]
            ]
            
            identification_table = Table(identification_data, colWidths=[2*inch, 4*inch])
            identification_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(identification_table)
            story.append(Spacer(1, 20))
        
        # BITCOIN ASSETS SECTION - ONLY INCLUDE ACTUAL FORM DATA
        story.append(Paragraph("ARTICLE VI - BITCOIN ASSETS", heading_style))
        
        if assets:
            # Digital Wallets - ONLY INCLUDE ACTUAL FORM FIELDS
            wallets = assets.get('wallets', [])
            if wallets and isinstance(wallets, list) and len(wallets) > 0:
                story.append(Paragraph("Digital Wallets:", bitcoin_heading_style))
                
                for i, wallet in enumerate(wallets, 1):
                    wallet_data = safe_json_parse(wallet, {})
                    
                    # ONLY INCLUDE FIELDS THAT EXIST IN THE FORM
                    if isinstance(wallet_data, dict):
                        wallet_info = [
                            [f'Wallet {i}:', ''],
                            ['Type:', wallet_data.get('type', 'N/A')],
                            ['Approximate Value:', wallet_data.get('value', 'N/A')],
                            ['Description:', wallet_data.get('description', 'N/A')],
                            ['Wallet Address (Public):', wallet_data.get('address', 'N/A')]
                        ]
                    else:
                        print(f"Warning: Wallet data is not a dict: {type(wallet_data)} = {wallet_data}")
                        wallet_info = [
                            [f'Wallet {i}:', ''],
                            ['Type:', 'N/A'],
                            ['Approximate Value:', 'N/A'],
                            ['Description:', 'N/A'],
                            ['Wallet Address (Public):', 'N/A']
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
            
            # Storage Information - ONLY INCLUDE ACTUAL FORM FIELDS
            if assets.get('storage_method') or assets.get('storage_location') or assets.get('storage_details'):
                story.append(Paragraph("Storage Information:", bitcoin_heading_style))
                
                storage_data = [
                    ['Storage Method:', assets.get('storage_method', 'N/A')],
                    ['Storage Location:', assets.get('storage_location', 'N/A')],
                    ['Additional Storage Details:', assets.get('storage_details', 'N/A')]
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
        
        # BENEFICIARIES SECTION - ONLY INCLUDE ACTUAL FORM DATA
        story.append(Paragraph("ARTICLE VII - BITCOIN ASSET BENEFICIARIES", heading_style))
        
        if beneficiaries:
            # Primary Beneficiaries - ONLY INCLUDE ACTUAL FORM FIELDS
            primary_beneficiaries = beneficiaries.get('primary', [])
            if primary_beneficiaries and isinstance(primary_beneficiaries, list) and len(primary_beneficiaries) > 0:
                story.append(Paragraph("Primary Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(primary_beneficiaries, 1):
                    beneficiary_data = safe_json_parse(beneficiary, {})
                    
                    # ONLY INCLUDE FIELDS THAT EXIST IN THE FORM
                    beneficiary_info = [
                        [f'Primary Beneficiary {i}:', ''],
                        ['Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Contact Information:', beneficiary_data.get('contact', 'N/A')]
                    ]
                    
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
            
            # Contingent Beneficiaries - ONLY INCLUDE ACTUAL FORM FIELDS
            contingent_beneficiaries = beneficiaries.get('contingent', [])
            if contingent_beneficiaries and isinstance(contingent_beneficiaries, list) and len(contingent_beneficiaries) > 0:
                story.append(Paragraph("Contingent Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(contingent_beneficiaries, 1):
                    beneficiary_data = safe_json_parse(beneficiary, {})
                    
                    # ONLY INCLUDE FIELDS THAT EXIST IN THE FORM
                    beneficiary_info = [
                        [f'Contingent Beneficiary {i}:', ''],
                        ['Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Contact Information:', beneficiary_data.get('contact', 'N/A')]
                    ]
                    
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
        
        # BITCOIN ASSET ACCESS INSTRUCTIONS SECTION - ONLY INCLUDE ACTUAL FORM DATA
        story.append(Paragraph("ARTICLE VIII - BITCOIN ASSET ACCESS INSTRUCTIONS", heading_style))
        
        if instructions:
            # Access Instructions - ONLY INCLUDE ACTUAL FORM FIELD
            if instructions.get('access_instructions'):
                story.append(Paragraph("Access Instructions:", bitcoin_heading_style))
                story.append(Paragraph(instructions.get('access_instructions', 'N/A'), body_style))
                story.append(Spacer(1, 10))
            
            # Security Notes - ONLY INCLUDE ACTUAL FORM FIELD
            if instructions.get('security_notes'):
                story.append(Paragraph("Security Notes:", bitcoin_heading_style))
                story.append(Paragraph(instructions.get('security_notes', 'N/A'), body_style))
                story.append(Spacer(1, 10))
            
            # Trusted Contacts - ONLY INCLUDE ACTUAL FORM FIELDS
            trusted_contacts = instructions.get('trusted_contacts', [])
            if trusted_contacts and isinstance(trusted_contacts, list) and len(trusted_contacts) > 0:
                story.append(Paragraph("Trusted Technical Contacts:", bitcoin_heading_style))
                
                for i, contact in enumerate(trusted_contacts, 1):
                    contact_data = safe_json_parse(contact, {})
                    
                    # ONLY INCLUDE FIELDS THAT EXIST IN THE FORM
                    contact_info = [
                        [f'Trusted Contact {i}:', ''],
                        ['Contact Name:', contact_data.get('name', 'N/A')],
                        ['Contact Information:', contact_data.get('info', 'N/A')]
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
        
        # LEGAL COMPLIANCE SECTION
        if legal_compliance:
            story.append(PageBreak())
            story.append(Paragraph("LEGAL COMPLIANCE & EXECUTION REQUIREMENTS", heading_style))
            
            # RUFADAA Compliance
            if legal_compliance.get('rufadaaConsent') or legal_compliance.get('digitalFiduciaryConsent'):
                story.append(Paragraph("DIGITAL ASSET AUTHORIZATION (RUFADAA COMPLIANCE)", subheading_style))
                
                if legal_compliance.get('rufadaaConsent'):
                    story.append(Paragraph("✓ I hereby grant my executor explicit authority to access, manage, and distribute my digital assets including Bitcoin and cryptocurrency holdings under the Revised Uniform Fiduciary Access to Digital Assets Act (RUFADAA).", body_style))
                    story.append(Spacer(1, 8))
                
                if legal_compliance.get('digitalFiduciaryConsent'):
                    story.append(Paragraph("✓ I consent to my executor accessing hardware wallets, software wallets, password managers, encrypted devices, and online exchange accounts as necessary for estate administration.", body_style))
                    story.append(Spacer(1, 15))
            
            # Legal Attestation
            if legal_compliance.get('primaryWillReference') or legal_compliance.get('addendumAttestation'):
                story.append(Paragraph("LEGAL ATTESTATION", subheading_style))
                
                if legal_compliance.get('primaryWillReference'):
                    story.append(Paragraph(f"Primary Will Reference: {legal_compliance.get('primaryWillReference')}", body_style))
                    story.append(Spacer(1, 8))
                
                if legal_compliance.get('addendumAttestation'):
                    story.append(Paragraph("✓ I attest that this Bitcoin Will Addendum is intended as an extension and supplement to my primary estate planning documents and should be read in conjunction with my primary will or trust.", body_style))
                    story.append(Spacer(1, 15))
            
            # Witness Requirements
            if legal_compliance.get('witness1Name') or legal_compliance.get('witness2Name'):
                story.append(Paragraph("WITNESS INFORMATION", subheading_style))
                
                witness_data = [
                    ['WITNESS 1', 'WITNESS 2'],
                    ['', ''],
                    [f"Name: {legal_compliance.get('witness1Name', '_' * 30)}", f"Name: {legal_compliance.get('witness2Name', '_' * 30)}"],
                    [f"Address: {legal_compliance.get('witness1Address', '_' * 30)}", f"Address: {legal_compliance.get('witness2Address', '_' * 30)}"],
                    ['', ''],
                    ['_' * 35, '_' * 35],
                    ['Witness 1 Signature', 'Witness 2 Signature'],
                    ['', ''],
                    ['Date: _______________', 'Date: _______________']
                ]
                
                witness_table = Table(witness_data, colWidths=[3*inch, 3*inch])
                witness_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ]))
                
                story.append(witness_table)
                story.append(Spacer(1, 15))
            
            # Notarization
            if legal_compliance.get('notarizationRequested'):
                story.append(Paragraph("NOTARIZATION SECTION", subheading_style))
                story.append(Paragraph("✓ This document is intended to be notarized for additional legal authentication.", body_style))
                
                if legal_compliance.get('notaryInstructions'):
                    story.append(Paragraph(f"Special Instructions: {legal_compliance.get('notaryInstructions')}", body_style))
                
                story.append(Spacer(1, 15))
        
        # ADDENDUM EXECUTION SECTION
        story.append(Paragraph("ADDENDUM EXECUTION", heading_style))
        
        execution_text = f"""I have executed this Bitcoin Asset Addendum this _____ day of _____________, 20___, as a supplement to my existing Last Will and Testament. This addendum shall be incorporated into and become part of my Last Will and Testament."""
        
        story.append(Paragraph(execution_text, body_style))
        story.append(Spacer(1, 30))
        
        # Signature lines for addendum
        signature_data = [
            ['', ''],
            ['_' * 40, '_' * 40],
            [f'{personal_info.get("full_name", "[TESTATOR NAME]")}', 'Date'],
            ['Testator Signature', ''],
            ['', ''],
            ['', ''],
            ['NOTARIZATION:', ''],
            ['', ''],
            ['State of: _________________________', ''],
            ['County of: _______________________', ''],
            ['', ''],
            ['On this _____ day of _____________, 20___, before me personally appeared'],
            [f'{personal_info.get("full_name", "[TESTATOR NAME]")}, who proved to me on the basis of satisfactory evidence'],
            ['to be the person whose name is subscribed to the within instrument and acknowledged'],
            ['to me that he/she executed the same in his/her authorized capacity, and that by his/her'],
            ['signature on the instrument the person, or the entity upon behalf of which the person'],
            ['acted, executed the instrument.', ''],
            ['', ''],
            ['_' * 40, ''],
            ['Notary Public Signature', ''],
            ['', ''],
            ['My commission expires: ___________', '']
        ]
        
        signature_table = Table(signature_data, colWidths=[4*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # ADDENDUM LEGAL NOTICE
        story.append(PageBreak())
        story.append(Paragraph("IMPORTANT LEGAL NOTICE", heading_style))
        
        disclaimer_text = """IMPORTANT LEGAL DISCLAIMER

This Bitcoin Asset Addendum is a document template designed to supplement an existing Last Will and Testament. 

NOT LEGAL ADVICE: This service does not provide legal advice, legal opinions, or legal services. We are a document preparation service only.

ATTORNEY CONSULTATION REQUIRED: It is strongly recommended that you consult with a qualified attorney licensed in your jurisdiction before executing this addendum. Estate planning laws vary significantly by state and country.

EXECUTION REQUIREMENTS: This addendum should be properly executed according to your state's requirements for will amendments or codicils. Some states may require this addendum to be witnessed and/or notarized. Please consult with legal counsel to ensure compliance with local laws.

BITCOIN LAW COMPLEXITY: Bitcoin laws are rapidly evolving and complex. Tax implications, inheritance laws, and regulatory requirements vary significantly. Professional legal and tax advice is essential.

NO WARRANTIES: We make no representations or warranties about the legal sufficiency, validity, or enforceability of any documents created using our service. Use at your own risk.

LIMITATION OF LIABILITY: The creators of this software disclaim any liability for the legal sufficiency or enforceability of this document. 

STORAGE: This addendum should be stored with your primary will and estate planning documents.

PROFESSIONAL CONSULTATION: We strongly recommend consulting with estate planning attorneys, tax professionals, financial advisors, and cryptocurrency specialists.

By using this document, you acknowledge that you understand these limitations and agree to seek appropriate professional legal advice."""
        
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
            try:
                # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
                will_dict = {
                    'id': will.id,
                    'user_id': will.user_id,
                    'title': will.title,
                    'personal_info': will.get_personal_info() if will.personal_info else {},
                    'bitcoin_assets': safe_decrypt_bitcoin_data(will.bitcoin_assets),
                    'beneficiaries': safe_decrypt_bitcoin_data(will.beneficiaries),
                    'executor_instructions': safe_decrypt_bitcoin_data(getattr(will, 'executor_instructions', None) or getattr(will, 'instructions', None)),
                    'status': will.status,
                    'created_at': will.created_at.isoformat() if will.created_at else None,
                    'updated_at': will.updated_at.isoformat() if will.updated_at else None
                }
                will_list.append(will_dict)
            except Exception as will_error:
                print(f"Error processing will {will.id}: {will_error}")
                # Skip this will and continue with others
                continue
        
        return jsonify({'wills': will_list}), 200
        
    except Exception as e:
        print(f"Error listing wills: {e}")
        import traceback
        traceback.print_exc()
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
            # Use correct field name - try executor_instructions first, fallback to instructions
            if hasattr(will, 'executor_instructions'):
                will.executor_instructions = encrypted_instructions
            else:
                will.instructions = encrypted_instructions
        if 'legal_compliance' in data:
            # ENCRYPT LEGAL COMPLIANCE DATA BEFORE STORAGE
            encrypted_compliance = encrypt_bitcoin_data(data['legal_compliance'])
            will.legal_compliance = encrypted_compliance
        
        db.session.add(will)
        db.session.commit()
        
        # Return will dict with decrypted data for frontend
        # AVOID CALLING will.to_dict() WHICH CAUSES JSON PARSE ERROR
        will_dict = {
            'id': will.id,
            'user_id': will.user_id,
            'title': will.title,
            'personal_info': will.get_personal_info(),
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': safe_decrypt_bitcoin_data(getattr(will, "executor_instructions", None) or getattr(will, "instructions", None)),
            'legal_compliance': decrypt_bitcoin_data(getattr(will, 'legal_compliance', None)) if getattr(will, 'legal_compliance', None) else {},
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
            'personal_info': will.get_personal_info(),
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': safe_decrypt_bitcoin_data(getattr(will, "executor_instructions", None) or getattr(will, "instructions", None)),
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
            # Use correct field name - try executor_instructions first, fallback to instructions
            if hasattr(will, 'executor_instructions'):
                will.executor_instructions = encrypted_instructions
            else:
                will.instructions = encrypted_instructions
        if 'legal_compliance' in data:
            # ENCRYPT LEGAL COMPLIANCE DATA BEFORE STORAGE
            encrypted_compliance = encrypt_bitcoin_data(data['legal_compliance'])
            will.legal_compliance = encrypted_compliance
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
            'personal_info': will.get_personal_info(),
            'bitcoin_assets': decrypt_bitcoin_data(will.bitcoin_assets) if will.bitcoin_assets else {},
            'beneficiaries': decrypt_bitcoin_data(will.beneficiaries) if will.beneficiaries else {},
            'executor_instructions': safe_decrypt_bitcoin_data(getattr(will, "executor_instructions", None) or getattr(will, "instructions", None)),
            'legal_compliance': decrypt_bitcoin_data(getattr(will, 'legal_compliance', None)) if getattr(will, 'legal_compliance', None) else {},
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
            'executor_instructions': getattr(will, "executor_instructions", None) or getattr(will, "instructions", None),  # Will be decrypted in PDF function
            'legal_compliance': getattr(will, 'legal_compliance', None)  # Will be decrypted in PDF function
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



# Main execution
if __name__ == '__main__':
    from flask import Flask
    from flask_cors import CORS
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bitcoin-will-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bitcoin_will.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprint
    app.register_blueprint(will_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    print("Starting Bitcoin Will backend server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

