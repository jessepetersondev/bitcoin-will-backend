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
        # FIXED: Use correct database field names
        assets = safe_json_parse(will_data.get('bitcoin_assets'), {})  # Changed from 'assets'
        beneficiaries = safe_json_parse(will_data.get('beneficiaries'), {})
        instructions = safe_json_parse(will_data.get('executor_instructions'), {})  # Changed from 'instructions'
        
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
                        [f'Primary Beneficiary {i}:', ''],
                        ['Full Name:', beneficiary_data.get('name', 'N/A')],
                        ['Relationship:', beneficiary_data.get('relationship', 'N/A')],
                        ['Percentage of Assets:', f"{beneficiary_data.get('percentage', '0')}%"],
                        ['Phone Number:', beneficiary_data.get('phone', 'N/A')],
                        ['Email Address:', beneficiary_data.get('email', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')]
                    ]
                    
                    # Add address information
                    ben_address = safe_json_parse(beneficiary_data.get('address'), {})
                    if ben_address:
                        beneficiary_info.extend([
                            ['Street Address:', ben_address.get('street', 'N/A')],
                            ['City:', ben_address.get('city', 'N/A')],
                            ['State/Province:', ben_address.get('state', 'N/A')],
                            ['ZIP/Postal Code:', ben_address.get('zip_code', 'N/A')],
                            ['Country:', ben_address.get('country', 'N/A')]
                        ])
                    
                    beneficiary_table = Table(beneficiary_info, colWidths=[1.8*inch, 4.2*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightcoral),
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
                        ['Percentage of Assets:', f"{beneficiary_data.get('percentage', '0')}%"],
                        ['Phone Number:', beneficiary_data.get('phone', 'N/A')],
                        ['Email Address:', beneficiary_data.get('email', 'N/A')],
                        ['Bitcoin Address:', beneficiary_data.get('bitcoin_address', 'N/A')]
                    ]
                    
                    # Add address information
                    ben_address = safe_json_parse(beneficiary_data.get('address'), {})
                    if ben_address:
                        beneficiary_info.extend([
                            ['Street Address:', ben_address.get('street', 'N/A')],
                            ['City:', ben_address.get('city', 'N/A')],
                            ['State/Province:', ben_address.get('state', 'N/A')],
                            ['ZIP/Postal Code:', ben_address.get('zip_code', 'N/A')],
                            ['Country:', ben_address.get('country', 'N/A')]
                        ])
                    
                    beneficiary_table = Table(beneficiary_info, colWidths=[1.8*inch, 4.2*inch])
                    beneficiary_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightsteelblue),
                    ]))
                    
                    story.append(beneficiary_table)
                    story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
        
        # EXECUTOR INSTRUCTIONS SECTION (ORIGINAL DETAILED FORMAT)
        story.append(Paragraph("ARTICLE VIII - EXECUTOR INSTRUCTIONS", heading_style))
        
        if instructions:
            # Access Instructions (ORIGINAL FORMAT)
            if instructions.get('access_instructions'):
                story.append(Paragraph("Access Instructions:", subheading_style))
                story.append(Paragraph(instructions.get('access_instructions'), body_style))
                story.append(Spacer(1, 10))
            
            # Security Notes (ORIGINAL FORMAT)
            if instructions.get('security_notes'):
                story.append(Paragraph("Security Notes:", subheading_style))
                story.append(Paragraph(instructions.get('security_notes'), body_style))
                story.append(Spacer(1, 10))
            
            # Additional Instructions (ORIGINAL FORMAT)
            if instructions.get('additional_instructions'):
                story.append(Paragraph("Additional Instructions:", subheading_style))
                story.append(Paragraph(instructions.get('additional_instructions'), body_style))
                story.append(Spacer(1, 10))
            
            # Emergency Contact (ORIGINAL FORMAT)
            if instructions.get('emergency_contact'):
                story.append(Paragraph("Emergency Contact:", subheading_style))
                story.append(Paragraph(instructions.get('emergency_contact'), body_style))
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
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightgoldenrodyellow),
                    ]))
                    
                    story.append(contact_table)
                    story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 30))
        
        # LEGAL CLOSING PROVISIONS
        story.append(Paragraph("ARTICLE IX - DIGITAL ASSET PROVISIONS", heading_style))
        story.append(Paragraph("I understand that digital assets, including Bitcoin and cryptocurrencies, require special handling due to their unique nature. I have provided detailed instructions for accessing these assets and authorize my Executor to engage qualified professionals as needed.", body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("ARTICLE X - EXECUTION AND WITNESSES", heading_style))
        story.append(Paragraph("IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of _____________, 20___, in the presence of the witnesses whose signatures appear below.", body_style))
        story.append(Spacer(1, 30))
        
        # Signature Section (ORIGINAL FORMAT)
        signature_data = [
            ['', '', ''],
            ['Testator Signature:', '_' * 40, 'Date: ___________'],
            ['', f"{personal_info.get('full_name', '[NAME]')}", ''],
            ['', '', ''],
            ['', '', ''],
            ['Witness 1 Signature:', '_' * 40, 'Date: ___________'],
            ['Print Name:', '_' * 40, ''],
            ['Address:', '_' * 40, ''],
            ['', '', ''],
            ['Witness 2 Signature:', '_' * 40, 'Date: ___________'],
            ['Print Name:', '_' * 40, ''],
            ['Address:', '_' * 40, ''],
        ]
        
        signature_table = Table(signature_data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # Legal Disclaimer
        story.append(Paragraph("LEGAL DISCLAIMER", subheading_style))
        story.append(Paragraph("This document is a template and may not be suitable for all jurisdictions. It is recommended to consult with a qualified attorney familiar with digital asset estate planning in your jurisdiction before executing this will.", body_style))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        raise e

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_will():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # FIXED: Use correct database field names
        new_will = Will(
            user_id=user.id,
            testator_name=data.get('personal_info', {}).get('full_name', ''),
            personal_info=json.dumps(data.get('personal_info', {})),
            bitcoin_assets=json.dumps(data.get('assets', {})),  # Correct field name
            beneficiaries=json.dumps(data.get('beneficiaries', {})),
            executor_instructions=json.dumps(data.get('instructions', {})),  # Correct field name
            status='draft'
        )
        
        db.session.add(new_will)
        db.session.commit()
        
        return jsonify({
            'message': 'Will created successfully',
            'will_id': new_will.id
        }), 201
        
    except Exception as e:
        print(f"Error creating will: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create will'}), 500

@will_bp.route('/list', methods=['GET', 'OPTIONS'])
@cross_origin()
def list_wills():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        wills = Will.query.filter_by(user_id=user.id).all()
        
        wills_data = []
        for will in wills:
            personal_info = safe_json_parse(will.personal_info)
            wills_data.append({
                'id': will.id,
                'title': f"Bitcoin Will - {personal_info.get('full_name', 'Unnamed')}",
                'testator_name': personal_info.get('full_name', 'Not specified'),
                'status': will.status,
                'created_at': will.created_at.isoformat() if will.created_at else None,
                'updated_at': will.updated_at.isoformat() if will.updated_at else None
            })
        
        return jsonify(wills_data), 200
        
    except Exception as e:
        print(f"Error listing wills: {str(e)}")
        return jsonify({'error': 'Failed to load wills'}), 500

@will_bp.route('/<int:will_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'error': 'Will not found'}), 404
        
        # FIXED: Use correct database field names
        will_data = {
            'id': will.id,
            'personal_info': safe_json_parse(will.personal_info),
            'assets': safe_json_parse(will.bitcoin_assets),  # Correct field name
            'beneficiaries': safe_json_parse(will.beneficiaries),
            'instructions': safe_json_parse(will.executor_instructions),  # Correct field name
            'status': will.status,
            'created_at': will.created_at.isoformat() if will.created_at else None,
            'updated_at': will.updated_at.isoformat() if will.updated_at else None
        }
        
        return jsonify(will_data), 200
        
    except Exception as e:
        print(f"Error getting will {will_id}: {str(e)}")
        return jsonify({'error': 'Failed to load will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def update_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'error': 'Will not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # FIXED: Use correct database field names
        will.testator_name = data.get('personal_info', {}).get('full_name', will.testator_name)
        will.personal_info = json.dumps(data.get('personal_info', {}))
        will.bitcoin_assets = json.dumps(data.get('assets', {}))  # Correct field name
        will.beneficiaries = json.dumps(data.get('beneficiaries', {}))
        will.executor_instructions = json.dumps(data.get('instructions', {}))  # Correct field name
        will.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Will updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating will {will_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'error': 'Will not found'}), 404
        
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting will {will_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete will'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET', 'OPTIONS'])
@cross_origin()
def download_will(will_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"Generating comprehensive legal PDF for will {will_id}")
        
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        if not will:
            return jsonify({'error': 'Will not found'}), 404
        
        # FIXED: Use correct database field names
        will_data = {
            'personal_info': will.personal_info,
            'bitcoin_assets': will.bitcoin_assets,  # Correct field name
            'beneficiaries': will.beneficiaries,
            'executor_instructions': will.executor_instructions  # Correct field name
        }
        
        # Generate comprehensive PDF with all details
        pdf_data = generate_comprehensive_bitcoin_will_pdf(will_data, user.email)
        
        # Create response
        response = send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'bitcoin_will_{will_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
        return response
        
    except Exception as e:
        print(f"Legal PDF generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate PDF'}), 500

