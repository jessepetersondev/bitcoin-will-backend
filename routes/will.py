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
                    ben_data = safe_json_parse(beneficiary, {})
                    ben_address = safe_json_parse(ben_data.get('address'), {})
                    
                    ben_info = [
                        [f'Beneficiary {i}:', ''],
                        ['Full Name:', ben_data.get('name', 'N/A')],
                        ['Relationship:', ben_data.get('relationship', 'N/A')],
                        ['Percentage of Assets:', f"{ben_data.get('percentage', 0)}%"],
                        ['Phone Number:', ben_data.get('phone', 'N/A')],
                        ['Email Address:', ben_data.get('email', 'N/A')],
                        ['Bitcoin Address:', ben_data.get('bitcoin_address', 'N/A')]
                    ]
                    
                    # Add address information if available
                    if ben_address:
                        ben_info.extend([
                            ['Street Address:', ben_address.get('street', 'N/A')],
                            ['City:', ben_address.get('city', 'N/A')],
                            ['State/Province:', ben_address.get('state', 'N/A')],
                            ['ZIP/Postal Code:', ben_address.get('zip_code', 'N/A')],
                            ['Country:', ben_address.get('country', 'N/A')]
                        ])
                    
                    ben_table = Table(ben_info, colWidths=[1.8*inch, 4.2*inch])
                    ben_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightgreen),
                    ]))
                    
                    story.append(ben_table)
                    story.append(Spacer(1, 10))
            
            # Contingent Beneficiaries (ORIGINAL DETAILED FORMAT)
            contingent_beneficiaries = beneficiaries.get('contingent', [])
            if contingent_beneficiaries and isinstance(contingent_beneficiaries, list) and len(contingent_beneficiaries) > 0:
                story.append(Paragraph("Contingent Beneficiaries:", bitcoin_heading_style))
                
                for i, beneficiary in enumerate(contingent_beneficiaries, 1):
                    ben_data = safe_json_parse(beneficiary, {})
                    
                    ben_info = [
                        [f'Contingent Beneficiary {i}:', ''],
                        ['Full Name:', ben_data.get('name', 'N/A')],
                        ['Relationship:', ben_data.get('relationship', 'N/A')],
                        ['Percentage:', f"{ben_data.get('percentage', 0)}%"],
                        ['Contact Information:', ben_data.get('contact', 'N/A')]
                    ]
                    
                    ben_table = Table(ben_info, colWidths=[1.8*inch, 4.2*inch])
                    ben_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, 0), colors.lightyellow),
                    ]))
                    
                    story.append(ben_table)
                    story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
        
        # INSTRUCTIONS SECTION (ORIGINAL DETAILED FORMAT)
        story.append(Paragraph("ARTICLE VIII - INSTRUCTIONS FOR EXECUTOR", heading_style))
        
        if instructions:
            if instructions.get('access_instructions'):
                story.append(Paragraph("Access Instructions:", bitcoin_heading_style))
                story.append(Paragraph(instructions['access_instructions'], styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('security_notes'):
                story.append(Paragraph("Security Notes:", bitcoin_heading_style))
                story.append(Paragraph(instructions['security_notes'], styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('trusted_contacts'):
                story.append(Paragraph("Trusted Contacts:", bitcoin_heading_style))
                
                trusted_contacts = instructions['trusted_contacts']
                if isinstance(trusted_contacts, list):
                    for contact in trusted_contacts:
                        contact_data = safe_json_parse(contact, {})
                        contact_info = [
                            ['Name:', contact_data.get('name', 'N/A')],
                            ['Contact Information:', contact_data.get('contact', 'N/A')],
                            ['Relationship:', contact_data.get('relationship', 'N/A')]
                        ]
                        
                        contact_table = Table(contact_info, colWidths=[1.5*inch, 4.5*inch])
                        contact_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ]))
                        
                        story.append(contact_table)
                        story.append(Spacer(1, 8))
        
        # ===== ADDITIONAL LEGAL PROVISIONS =====
        
        story.append(Spacer(1, 20))
        
        # LEGAL DISTRIBUTION METHODS
        story.append(Paragraph("ARTICLE IX - DISTRIBUTION METHODS", heading_style))
        distribution_text = """My Executor may distribute digital assets to beneficiaries through any of the following methods: (a) Direct transfer of cryptocurrency to beneficiary-controlled wallets; (b) Conversion to traditional currency and distribution of cash proceeds; (c) Transfer of physical storage devices containing digital assets; (d) Any combination of the above methods as circumstances require."""
        story.append(Paragraph(distribution_text, body_style))
        story.append(Spacer(1, 15))
        
        # TAX COMPLIANCE
        story.append(Paragraph("ARTICLE X - TAX AND REGULATORY COMPLIANCE", heading_style))
        tax_text = """I acknowledge that my digital assets may be subject to federal and state income taxes, estate taxes, and capital gains taxes. I authorize my Executor to engage qualified tax professionals and make any elections that may reduce the overall tax burden on my estate and beneficiaries."""
        story.append(Paragraph(tax_text, body_style))
        story.append(Spacer(1, 15))
        
        # FIDUCIARY PROTECTIONS
        story.append(Paragraph("ARTICLE XI - FIDUCIARY PROTECTIONS", heading_style))
        protection_text = """I acknowledge that digital assets are subject to extreme price volatility and technical risks. My Executor shall not be liable for any decrease in value of digital assets during estate administration, provided that the Executor acts in good faith and with reasonable care."""
        story.append(Paragraph(protection_text, body_style))
        story.append(Spacer(1, 15))
        
        # NO-CONTEST CLAUSE
        story.append(Paragraph("ARTICLE XII - NO-CONTEST PROVISION", heading_style))
        no_contest_text = """If any beneficiary contests this Will or challenges any action taken by my Executor regarding digital assets, and such contest is unsuccessful, that beneficiary shall forfeit all rights to any distribution under this Will."""
        story.append(Paragraph(no_contest_text, body_style))
        story.append(Spacer(1, 15))
        
        # RESIDUARY CLAUSE
        story.append(Paragraph("ARTICLE XIII - RESIDUARY ESTATE", heading_style))
        residuary_text = """All the rest, residue, and remainder of my estate, including any digital assets not specifically disposed of above, I give to my primary beneficiaries in the same proportions as specified for my digital assets."""
        story.append(Paragraph(residuary_text, body_style))
        story.append(Spacer(1, 30))
        
        # EXECUTION SECTION (ENHANCED FROM ORIGINAL)
        story.append(Paragraph("ARTICLE XIV - EXECUTION", heading_style))
        
        execution_text = f"""IN WITNESS WHEREOF, I have hereunto set my hand and seal this _____ day of _____________, 20___, at {city}, {state}."""
        story.append(Paragraph(execution_text, body_style))
        story.append(Spacer(1, 30))
        
        # SIGNATURE SECTION (ORIGINAL FORMAT ENHANCED)
        signature_data = [
            ['', '', ''],
            ['_' * 50, '', 'Testator'],
            [testator_name, '', ''],
            ['', '', ''],
            ['', '', ''],
            ['WITNESSES:', '', ''],
            ['', '', ''],
            ['We, the undersigned witnesses, each do hereby declare', '', ''],
            ['in the presence of the aforesaid Testator and in the', '', ''],
            ['presence of each other, that the Testator signed and', '', ''],
            ['executed this instrument as the Testator\'s Last Will', '', ''],
            ['and Testament.', '', ''],
            ['', '', ''],
            ['_' * 40, '    ', '_' * 40],
            ['Witness #1 Signature', '    ', 'Witness #2 Signature'],
            ['', '', ''],
            ['_' * 40, '    ', '_' * 40],
            ['Print Name', '    ', 'Print Name'],
            ['', '', ''],
            ['_' * 40, '    ', '_' * 40],
            ['Address', '    ', 'Address'],
            ['', '', ''],
            ['_' * 40, '    ', '_' * 40],
            ['Date', '    ', 'Date'],
            ['', '', ''],
            ['', '', ''],
            ['NOTARY:', '', ''],
            ['', '', ''],
            ['_' * 40, '    ', '_' * 20],
            ['Notary Signature', '    ', 'Date'],
            ['', '', ''],
            ['Notary Seal:', '', '']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 0.5*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(signature_table)
        story.append(PageBreak())
        
        # SELF-PROVING AFFIDAVIT
        story.append(Paragraph("SELF-PROVING AFFIDAVIT", title_style))
        story.append(Spacer(1, 20))
        
        affidavit_text = f"""STATE OF {state.upper()}
COUNTY OF {city.upper()}

We, {testator_name}, the Testator, and the undersigned witnesses, being first duly sworn, do hereby declare that the Testator signed and executed the instrument as the Testator's Last Will and Testament, and that each of the witnesses signed the Will as witness in the presence and hearing of the Testator.

_________________________________
{testator_name}, Testator

_________________________________
Witness

_________________________________
Witness

Subscribed, sworn to and acknowledged before me by {testator_name}, the Testator, and subscribed and sworn to before me by the above-named witnesses, this _____ day of _____________, 20___.

_________________________________
Notary Public
My commission expires: ___________"""
        
        story.append(Paragraph(affidavit_text, body_style))
        story.append(Spacer(1, 30))
        
        # FOOTER
        footer_text = f"This comprehensive Bitcoin Will was generated on {datetime.now().strftime('%B %d, %Y')} and includes both detailed asset information and legal compliance provisions. This document should be reviewed by a qualified estate planning attorney before execution."
        
        story.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Comprehensive Bitcoin will PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


# Route handlers - PRESERVED FROM ORIGINAL IMPLEMENTATION

@will_bp.route('/list', methods=['GET', 'OPTIONS'])
@cross_origin()
def list_wills():
    """Get user's wills - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        wills = Will.query.filter_by(user_id=user.id).all()
        
        return jsonify({
            'wills': [will.to_dict() for will in wills]
        }), 200
        
    except Exception as e:
        print(f"List wills error: {e}")
        return jsonify({'message': 'Failed to get wills'}), 500

@will_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_will():
    """Create a new will - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
        
        # Create new will
        will = Will(
            user_id=user.id,
            title=data.get('title', 'My Bitcoin Will'),
            status='draft'
        )
        
        # Set JSON data
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            will.set_bitcoin_assets(data['assets'])
        if 'beneficiaries' in data:
            will.set_beneficiaries(data['beneficiaries'])
        if 'instructions' in data:
            will.set_instructions(data['instructions'])
        
        db.session.add(will)
        db.session.commit()
        
        return jsonify({
            'message': 'Will created successfully',
            'will': will.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create will error: {e}")
        return jsonify({'message': 'Failed to create will'}), 500

@will_bp.route('/<int:will_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_will(will_id):
    """Get a specific will - ENHANCED FOR EDITING"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        # Return complete will data for editing
        will_dict = will.to_dict()
        
        # Ensure all sections exist for frontend form population
        if 'personal_info' not in will_dict:
            will_dict['personal_info'] = {}
        if 'assets' not in will_dict:
            will_dict['assets'] = {'wallets': []}
        if 'beneficiaries' not in will_dict:
            will_dict['beneficiaries'] = {'primary': [], 'contingent': []}
        if 'instructions' not in will_dict:
            will_dict['instructions'] = {'trusted_contacts': []}
        
        print(f"Returning will data for editing: {will_dict}")
        
        return jsonify({'will': will_dict}), 200
        
    except Exception as e:
        print(f"Get will error: {e}")
        return jsonify({'message': 'Failed to get will'}), 500

@will_bp.route('/<int:will_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def update_will(will_id):
    """Update a will - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
        
        print(f"Updating will {will_id} with data: {data}")
        
        # Update will data
        if 'title' in data:
            will.title = data['title']
        if 'personal_info' in data:
            will.set_personal_info(data['personal_info'])
        if 'assets' in data:
            will.set_bitcoin_assets(data['assets'])
        if 'beneficiaries' in data:
            will.set_beneficiaries(data['beneficiaries'])
        if 'instructions' in data:
            will.set_instructions(data['instructions'])
        if 'status' in data:
            will.status = data['status']
        
        will.updated_at = datetime.utcnow()
        db.session.commit()
        
        print(f"Will {will_id} updated successfully")
        
        return jsonify({
            'message': 'Will updated successfully',
            'will': will.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update will error: {e}")
        return jsonify({'message': 'Failed to update will'}), 500

@will_bp.route('/<int:will_id>/download', methods=['GET', 'OPTIONS'])
@cross_origin()
def download_will(will_id):
    """Download will as comprehensive Bitcoin will PDF with ALL details + legal framework"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        print(f"Generating comprehensive Bitcoin will PDF with ALL details for will {will_id}")
        
        # Get will data - Use the model methods that return parsed data
        will_data = {
            'personal_info': will.get_personal_info(),
            'assets': will.get_bitcoin_assets(),
            'beneficiaries': will.get_beneficiaries(),
            'instructions': will.get_instructions()
        }
        
        print(f"Will data structure: {will_data}")
        
        # Generate comprehensive Bitcoin will PDF with ALL original details + legal framework
        pdf_buffer = generate_comprehensive_bitcoin_will_pdf(will_data, user.email)
        
        if not pdf_buffer:
            return jsonify({'message': 'Failed to generate comprehensive Bitcoin will PDF'}), 500
        
        # Return PDF file with descriptive naming
        safe_title = will.title.replace(' ', '_').replace('/', '_')
        filename = f"Comprehensive_Bitcoin_Will_{safe_title}_{will_id}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Download comprehensive Bitcoin will error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Failed to download comprehensive Bitcoin will'}), 500

@will_bp.route('/<int:will_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_will(will_id):
    """Delete a will - PRESERVED WORKING CODE"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        db.session.delete(will)
        db.session.commit()
        
        return jsonify({'message': 'Will deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete will error: {e}")
        return jsonify({'message': 'Failed to delete will'}), 500

