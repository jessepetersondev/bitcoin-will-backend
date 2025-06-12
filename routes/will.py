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

will_bp = Blueprint('will', __name__)

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
        
        # Parse all JSON fields safely
        personal_info = safe_json_parse(will_data.get('personal_info'), {})
        assets = safe_json_parse(will_data.get('assets'), {})
        beneficiaries = safe_json_parse(will_data.get('beneficiaries'), {})
        instructions = safe_json_parse(will_data.get('instructions'), {})
        
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
                    beneficiary_address = safe_json_parse(beneficiary_data.get('address'), {})
                    
                    beneficiary_info = [
                        [f'Primary Beneficiary {i}:', ''],
                        ['Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Phone:', beneficiary_data.get('phone', 'N/A')],
                        ['Email:', beneficiary_data.get('email', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')],
                        ['Street Address:', beneficiary_address.get('street', 'N/A')],
                        ['City:', beneficiary_address.get('city', 'N/A')],
                        ['State/Province:', beneficiary_address.get('state', 'N/A')],
                        ['ZIP/Postal Code:', beneficiary_address.get('zip_code', 'N/A')],
                        ['Country:', beneficiary_address.get('country', 'N/A')]
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
            
            # Contingent Beneficiaries (ORIGINAL DETAILED FORMAT)
            contingent_beneficiaries = beneficiaries.get('contingent', [])
            if contingent_beneficiaries and isinstance(contingent_beneficiaries, list) and len(contingent_beneficiaries) > 0:
                story.append(Paragraph("Contingent Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(contingent_beneficiaries, 1):
                    beneficiary_data = safe_json_parse(beneficiary, {})
                    beneficiary_address = safe_json_parse(beneficiary_data.get('address'), {})
                    
                    beneficiary_info = [
                        [f'Contingent Beneficiary {i}:', ''],
                        ['Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary_data.get('percentage', 'N/A')}%"],
                        ['Phone:', beneficiary_data.get('phone', 'N/A')],
                        ['Email:', beneficiary_data.get('email', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')],
                        ['Street Address:', beneficiary_address.get('street', 'N/A')],
                        ['City:', beneficiary_address.get('city', 'N/A')],
                        ['State/Province:', beneficiary_address.get('state', 'N/A')],
                        ['ZIP/Postal Code:', beneficiary_address.get('zip_code', 'N/A')],
                        ['Country:', beneficiary_address.get('country', 'N/A')]
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
        
        # INSTRUCTIONS SECTION (ORIGINAL DETAILED FORMAT)
        story.append(Paragraph("ARTICLE VIII - ACCESS INSTRUCTIONS AND SECURITY", heading_style))
        
        if instructions:
            instructions_data = [
                ['Access Instructions:', instructions.get('access_instructions', 'N/A')],
                ['Security Notes:', instructions.get('security_notes', 'N/A')],
                ['Additional Instructions:', instructions.get('additional_instructions', 'N/A')],
                ['Emergency Contact:', instructions.get('emergency_contact', 'N/A')]
            ]
            
            instructions_table = Table(instructions_data, colWidths=[2*inch, 4*inch])
            instructions_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(instructions_table)
            story.append(Spacer(1, 15))
            
            # Trusted Contacts (ORIGINAL DETAILED FORMAT)
            trusted_contacts = instructions.get('trusted_contacts', [])
            if trusted_contacts and isinstance(trusted_contacts, list) and len(trusted_contacts) > 0:
                story.append(Paragraph("Trusted Contacts:", bitcoin_heading_style))
                
                for i, contact in enumerate(trusted_contacts, 1):
                    contact_data = safe_json_parse(contact, {})
                    
                    contact_info = [
                        [f'Trusted Contact {i}:', ''],
                        ['Name:', contact_data.get('name', 'N/A')],
                        ['Contact Information:', contact_data.get('contact', 'N/A')],
                        ['Relationship:', contact_data.get('relationship', 'N/A')],
                        ['Role/Expertise:', contact_data.get('role', 'N/A')]
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
        
        # ===== LEGAL FRAMEWORK CONTINUES =====
        
        # CRYPTOCURRENCY SPECIFIC PROVISIONS
        story.append(Paragraph("ARTICLE IX - CRYPTOCURRENCY SPECIFIC PROVISIONS", heading_style))
        
        crypto_provisions = [
            "I acknowledge that cryptocurrency assets are highly volatile and may fluctuate significantly in value between the date of this Will and the date of my death.",
            "I direct my Executor to engage qualified cryptocurrency experts to assist with the recovery and transfer of digital assets.",
            "My Executor is authorized to convert cryptocurrency assets to fiat currency if necessary for estate administration or distribution to beneficiaries.",
            "All private keys, seed phrases, and access credentials referenced in this Will should be treated with the highest level of security and confidentiality."
        ]
        
        for provision in crypto_provisions:
            story.append(Paragraph(provision, clause_style))
        
        story.append(Spacer(1, 15))
        
        # EXECUTOR POWERS
        story.append(Paragraph("ARTICLE X - EXECUTOR POWERS", heading_style))
        
        executor_powers = [
            "To access all digital wallets, exchanges, and cryptocurrency accounts listed in this Will.",
            "To engage technical experts, including blockchain specialists and cryptocurrency recovery services.",
            "To convert digital assets to fiat currency when necessary for estate administration.",
            "To establish new cryptocurrency wallets or accounts for the purpose of asset distribution.",
            "To execute all necessary technical procedures for the transfer of digital assets to beneficiaries."
        ]
        
        for power in executor_powers:
            story.append(Paragraph(power, clause_style))
        
        story.append(Spacer(1, 15))
        
        # FIDUCIARY PROTECTION
        story.append(Paragraph("ARTICLE XI - FIDUCIARY PROTECTION", heading_style))
        story.append(Paragraph("My Executor shall not be held liable for any loss in value of cryptocurrency assets due to market volatility, technological failures, or other factors beyond their reasonable control, provided they act in good faith and with reasonable care.", body_style))
        story.append(Spacer(1, 15))
        
        # TAX CONSIDERATIONS
        story.append(Paragraph("ARTICLE XII - TAX CONSIDERATIONS", heading_style))
        story.append(Paragraph("I direct my Executor to consult with qualified tax professionals regarding the tax implications of cryptocurrency transfers and to ensure compliance with all applicable tax laws and reporting requirements.", body_style))
        story.append(Spacer(1, 15))
        
        # NO CONTEST CLAUSE
        story.append(Paragraph("ARTICLE XIII - NO CONTEST CLAUSE", heading_style))
        story.append(Paragraph("If any beneficiary contests this Will or any of its provisions, that beneficiary shall forfeit any interest in my estate and shall be treated as if they predeceased me.", body_style))
        story.append(Spacer(1, 15))
        
        # SIMULTANEOUS DEATH
        story.append(Paragraph("ARTICLE XIV - SIMULTANEOUS DEATH", heading_style))
        story.append(Paragraph("If any beneficiary and I die under circumstances that make it difficult or impossible to determine who died first, it shall be presumed that the beneficiary predeceased me.", body_style))
        story.append(Spacer(1, 15))
        
        # LEGAL DISCLAIMER
        story.append(Paragraph("ARTICLE XV - LEGAL DISCLAIMER", heading_style))
        story.append(Paragraph("This Will has been prepared using automated tools and should be reviewed by a qualified attorney familiar with estate planning and cryptocurrency law in the applicable jurisdiction. Laws regarding digital assets vary by location and continue to evolve.", body_style))
        story.append(Spacer(1, 30))
        
        # SIGNATURE SECTION
        story.append(Paragraph("EXECUTION AND ATTESTATION", heading_style))
        
        signature_text = f"""IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of _____________, 20___, at ________________, ________________."""
        
        story.append(Paragraph(signature_text, body_style))
        story.append(Spacer(1, 30))
        
        # Signature lines
        signature_lines = [
            ['', ''],
            ['_' * 40, ''],
            [f'{personal_info.get("full_name", "[TESTATOR NAME]")}', ''],
            ['Testator', '']
        ]
        
        signature_table = Table(signature_lines, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # WITNESS SECTION
        story.append(Paragraph("WITNESS ATTESTATION", subheading_style))
        
        witness_text = """We, the undersigned witnesses, each do hereby declare in the presence of the aforesaid testator that the testator signed and executed this instrument as the testator's Last Will and Testament and that each of us, in the hearing and sight of the testator, hereby signs this Will as witness to the testator's signing, and that to the best of our knowledge the testator is eighteen years of age or over, of sound mind, and under no constraint or undue influence."""
        
        story.append(Paragraph(witness_text, body_style))
        story.append(Spacer(1, 20))
        
        # Witness signature lines
        witness_lines = [
            ['Witness 1:', 'Witness 2:'],
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Signature', 'Signature'],
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Print Name', 'Print Name'],
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Address', 'Address'],
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Date', 'Date']
        ]
        
        witness_table = Table(witness_lines, colWidths=[3*inch, 3*inch])
        witness_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(witness_table)
        story.append(Spacer(1, 30))
        
        # NOTARY SECTION
        story.append(Paragraph("NOTARY ACKNOWLEDGMENT", subheading_style))
        
        notary_text = """State of ________________
County of ________________

On this _____ day of _____________, 20___, before me personally appeared the above-named testator and witnesses, who proved to me on the basis of satisfactory evidence to be the persons whose names are subscribed to the within instrument and acknowledged to me that they executed the same in their authorized capacities, and that by their signatures on the instrument the persons, or the entity upon behalf of which the persons acted, executed the instrument.

I certify under PENALTY OF PERJURY under the laws of the State of ________________ that the foregoing paragraph is true and correct.

WITNESS my hand and official seal.


_________________________________
Notary Public"""
        
        story.append(Paragraph(notary_text, body_style))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise e

# MODIFIED: Session-only will creation endpoint (NO DATABASE STORAGE)
@will_bp.route('/create-session', methods=['POST'])
@cross_origin()
def create_session_will():
    """Create will from session data without storing Bitcoin information in database"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        print(f"Creating session-only will for user {user.id}")
        
        # Generate PDF directly from session data (NO DATABASE STORAGE)
        pdf_data = generate_comprehensive_bitcoin_will_pdf(data, user.email)
        
        # Create a temporary file for download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_will_{user.id}_{timestamp}.pdf"
        
        # Return PDF as download
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Session will creation error: {e}")
        return jsonify({'message': 'Failed to create will'}), 500

# PRESERVED: All original endpoints for backward compatibility
@will_bp.route('/create', methods=['POST'])
@cross_origin()
def create_will():
    """PRESERVED: Original create will endpoint - NO LONGER STORES BITCOIN DATA"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        print(f"Creating will for user {user.id} - Bitcoin data will NOT be stored")
        
        # Create will record with only basic info (NO BITCOIN DATA)
        will = Will(
            user_id=user.id,
            title=data.get('title', f'Bitcoin Will - {datetime.now().strftime("%Y-%m-%d")}'),
            personal_info=json.dumps(data.get('personal_info', {})),
            # SECURITY: Bitcoin data fields left empty
            assets=json.dumps({}),  # Empty - no Bitcoin data stored
            beneficiaries=json.dumps({}),  # Empty - no Bitcoin data stored  
            instructions=json.dumps({}),  # Empty - no Bitcoin data stored
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(will)
        db.session.commit()
        
        # Generate PDF with session data (not stored data)
        pdf_data = generate_comprehensive_bitcoin_will_pdf(data, user.email)
        
        # Create a temporary file for download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_will_{will.id}_{timestamp}.pdf"
        
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Will creation error: {e}")
        return jsonify({'message': 'Failed to create will'}), 500

@will_bp.route('/list', methods=['GET'])
@cross_origin()
def list_wills():
    """PRESERVED: List user's wills (only shows basic info, no Bitcoin data)"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        wills = Will.query.filter_by(user_id=user.id).order_by(Will.created_at.desc()).all()
        
        will_list = []
        for will in wills:
            personal_info = safe_json_parse(will.personal_info, {})
            
            will_list.append({
                'id': will.id,
                'title': will.title,
                'created_at': will.created_at.isoformat() if will.created_at else None,
                'updated_at': will.updated_at.isoformat() if will.updated_at else None,
                'testator_name': personal_info.get('full_name', 'Unknown'),
                # SECURITY: No Bitcoin data returned
                'has_bitcoin_data': False  # Always false for security
            })
        
        return jsonify(will_list), 200
        
    except Exception as e:
        print(f"Will list error: {e}")
        return jsonify({'message': 'Failed to retrieve wills'}), 500

@will_bp.route('/<int:will_id>', methods=['GET'])
@cross_origin()
def get_will(will_id):
    """PRESERVED: Get will details (only personal info, no Bitcoin data)"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # Return only personal info for security
        return jsonify({
            'id': will.id,
            'title': will.title,
            'personal_info': safe_json_parse(will.personal_info, {}),
            # SECURITY: Bitcoin data not returned
            'assets': {},
            'beneficiaries': {},
            'instructions': {},
            'created_at': will.created_at.isoformat() if will.created_at else None,
            'updated_at': will.updated_at.isoformat() if will.updated_at else None
        }), 200
        
    except Exception as e:
        print(f"Get will error: {e}")
        return jsonify({'message': 'Failed to retrieve will'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET'])
@cross_origin()
def download_will(will_id):
    """PRESERVED: Download will PDF (generates from stored personal info only)"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        print(f"Generating PDF for will {will_id} - using stored personal info only")
        
        # Generate PDF with only stored personal info (no Bitcoin data)
        will_data = {
            'personal_info': safe_json_parse(will.personal_info, {}),
            'assets': {},  # Empty for security
            'beneficiaries': {},  # Empty for security
            'instructions': {}  # Empty for security
        }
        
        pdf_data = generate_comprehensive_bitcoin_will_pdf(will_data, user.email)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_will_{will.id}_{timestamp}.pdf"
        
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Will download error: {e}")
        return jsonify({'message': 'Failed to download will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT'])
@cross_origin()
def update_will(will_id):
    """PRESERVED: Update will (only updates personal info, no Bitcoin data stored)"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        print(f"Updating will {will_id} - only personal info will be stored")
        
        # Update only personal info and title (NO BITCOIN DATA)
        if 'title' in data:
            will.title = data['title']
        
        if 'personal_info' in data:
            will.personal_info = json.dumps(data['personal_info'])
        
        # SECURITY: Bitcoin data fields remain empty
        will.assets = json.dumps({})
        will.beneficiaries = json.dumps({})
        will.instructions = json.dumps({})
        
        will.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Will updated successfully (personal info only)'}), 200
        
    except Exception as e:
        print(f"Will update error: {e}")
        return jsonify({'message': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE'])
@cross_origin()
def delete_will(will_id):
    """PRESERVED: Delete will"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        print(f"Will deletion error: {e}")
        return jsonify({'message': 'Failed to delete will'}), 500

