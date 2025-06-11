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

def generate_legal_will_pdf(will_data, user_email):
    """Generate comprehensive legal Bitcoin will PDF with all required clauses"""
    try:
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
        
        # Define comprehensive styles for legal document
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'LegalTitle',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        # Main heading style
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
        
        # Subheading style
        subheading_style = ParagraphStyle(
            'LegalSubheading',
            parent=styles['Heading3'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.black
        )
        
        # Body text style
        body_style = ParagraphStyle(
            'LegalBody',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            textColor=colors.black
        )
        
        # Clause style for numbered provisions
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
        
        # Build the comprehensive legal document
        story = []
        
        # Document Title
        story.append(Paragraph("LAST WILL AND TESTAMENT", title_style))
        story.append(Paragraph("OF", title_style))
        
        personal_info = will_data.get('personal_info', {})
        testator_name = personal_info.get('full_name', 'UNKNOWN').upper()
        story.append(Paragraph(testator_name, title_style))
        story.append(Spacer(1, 30))
        
        # Opening Declaration
        story.append(Paragraph("ARTICLE I - DECLARATION", heading_style))
        
        opening_text = f"""I, {personal_info.get('full_name', '[NAME]')}, a resident of {personal_info.get('address', {}).get('city', '[CITY]')}, {personal_info.get('address', {}).get('state', '[STATE]')}, being of sound mind and disposing memory, and not acting under duress, menace, fraud, or undue influence of any person whomsoever, do hereby make, publish, and declare this to be my Last Will and Testament, hereby expressly revoking all former wills and codicils by me at any time heretofore made."""
        
        story.append(Paragraph(opening_text, body_style))
        story.append(Spacer(1, 15))
        
        # Revocation Clause
        story.append(Paragraph("ARTICLE II - REVOCATION OF PRIOR WILLS", heading_style))
        
        revocation_text = """I hereby revoke all wills, codicils, and other testamentary dispositions heretofore made by me. This Will shall supersede and replace any and all prior testamentary documents, and I declare this to be my only valid Last Will and Testament."""
        
        story.append(Paragraph(revocation_text, body_style))
        story.append(Spacer(1, 15))
        
        # Testamentary Capacity Declaration
        story.append(Paragraph("ARTICLE III - TESTAMENTARY CAPACITY", heading_style))
        
        capacity_text = """I declare that I am of sound mind and memory, that I have full testamentary capacity, and that I understand the nature and extent of my property and the natural objects of my bounty. I am not acting under any constraint or undue influence, and this Will expresses my true wishes concerning the disposition of my property upon my death."""
        
        story.append(Paragraph(capacity_text, body_style))
        story.append(Spacer(1, 15))
        
        # Executor Appointment
        story.append(Paragraph("ARTICLE IV - APPOINTMENT OF EXECUTOR", heading_style))
        
        executor_name = personal_info.get('executor_name', '[EXECUTOR NAME]')
        executor_contact = personal_info.get('executor_contact', '[EXECUTOR CONTACT]')
        
        executor_text = f"""I hereby nominate and appoint {executor_name} as the Executor of this Will. If {executor_name} is unable or unwilling to serve, I nominate [ALTERNATE EXECUTOR] as alternate Executor. I direct that no bond or other security shall be required of any Executor appointed hereunder."""
        
        story.append(Paragraph(executor_text, body_style))
        story.append(Spacer(1, 10))
        
        # Executor Powers
        story.append(Paragraph("Powers of Executor:", subheading_style))
        
        powers_text = """I grant to my Executor the following powers, to be exercised in their sole discretion and without court approval:
        
        (a) To access, manage, and distribute all digital assets, including but not limited to Bitcoin, cryptocurrencies, digital tokens, and blockchain-based assets;
        
        (b) To obtain possession of private keys, seed phrases, passwords, and other authentication credentials necessary to access digital assets;
        
        (c) To engage technical experts, cryptocurrency specialists, and professional advisors as necessary for the proper management and distribution of digital assets;
        
        (d) To convert digital assets to traditional currency when deemed necessary or appropriate for estate administration or beneficiary needs;
        
        (e) To make all decisions regarding the timing, method, and manner of digital asset distribution;
        
        (f) To execute all documents and take all actions necessary to effectuate the transfer of digital assets to beneficiaries."""
        
        story.append(Paragraph(powers_text, body_style))
        story.append(Spacer(1, 15))
        
        # Digital Assets Article
        story.append(Paragraph("ARTICLE V - DIGITAL ASSETS AND CRYPTOCURRENCY", heading_style))
        
        digital_assets_intro = """For purposes of this Will, "digital assets" shall include, but not be limited to, Bitcoin, other cryptocurrencies, digital tokens, non-fungible tokens (NFTs), and any other form of digital property stored on blockchain networks or similar distributed ledger technologies."""
        
        story.append(Paragraph(digital_assets_intro, body_style))
        story.append(Spacer(1, 10))
        
        # Digital Asset Inventory
        story.append(Paragraph("Digital Asset Inventory:", subheading_style))
        
        assets = will_data.get('assets', {})
        if assets and assets.get('wallets'):
            story.append(Paragraph("I own the following digital wallets and cryptocurrency holdings:", body_style))
            
            for i, wallet in enumerate(assets['wallets'], 1):
                wallet_info = f"""Wallet {i}: {wallet.get('type', 'Unknown')} wallet described as "{wallet.get('description', 'No description')}" with access method: {wallet.get('access_method', 'See separate access guide')}."""
                story.append(Paragraph(wallet_info, clause_style))
        
        # Access Instructions Reference
        story.append(Spacer(1, 10))
        story.append(Paragraph("Access Instructions:", subheading_style))
        
        access_text = """I acknowledge that access to my digital assets requires possession of private keys, seed phrases, passwords, and other authentication credentials. I have created a separate Digital Asset Access Guide that provides detailed instructions for accessing these credentials. This Guide is incorporated by reference into this Will and should be treated as confidential information accessible only to my Executor and designated beneficiaries."""
        
        story.append(Paragraph(access_text, body_style))
        story.append(Spacer(1, 15))
        
        # Beneficiaries Article
        story.append(Paragraph("ARTICLE VI - BENEFICIARIES AND DISTRIBUTION", heading_style))
        
        beneficiaries = will_data.get('beneficiaries', {})
        primary_beneficiaries = beneficiaries.get('primary', [])
        
        if primary_beneficiaries:
            story.append(Paragraph("I give, devise, and bequeath my digital assets as follows:", body_style))
            
            for i, beneficiary in enumerate(primary_beneficiaries, 1):
                ben_name = beneficiary.get('name', '[BENEFICIARY NAME]')
                ben_relationship = beneficiary.get('relationship', '[RELATIONSHIP]')
                ben_percentage = beneficiary.get('percentage', 0)
                
                ben_text = f"""{i}. To {ben_name}, my {ben_relationship}, {ben_percentage}% of all my digital assets and cryptocurrency holdings."""
                
                story.append(Paragraph(ben_text, clause_style))
                
                # Add beneficiary contact information
                if beneficiary.get('contact'):
                    contact_text = f"Contact information: {beneficiary.get('contact', '')}"
                    story.append(Paragraph(contact_text, clause_style))
        
        # Contingent Beneficiaries
        contingent_beneficiaries = beneficiaries.get('contingent', [])
        if contingent_beneficiaries:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Contingent Beneficiaries:", subheading_style))
            
            contingent_text = """If any primary beneficiary predeceases me or is unable to receive their distribution, their share shall pass to the following contingent beneficiaries:"""
            story.append(Paragraph(contingent_text, body_style))
            
            for i, beneficiary in enumerate(contingent_beneficiaries, 1):
                ben_name = beneficiary.get('name', '[CONTINGENT BENEFICIARY]')
                ben_relationship = beneficiary.get('relationship', '[RELATIONSHIP]')
                ben_percentage = beneficiary.get('percentage', 0)
                
                ben_text = f"""{i}. {ben_name}, my {ben_relationship}, to receive {ben_percentage}% of the deceased beneficiary's share."""
                story.append(Paragraph(ben_text, clause_style))
        
        story.append(Spacer(1, 15))
        
        # Distribution Methods
        story.append(Paragraph("Distribution Methods:", subheading_style))
        
        distribution_text = """My Executor may distribute digital assets to beneficiaries through any of the following methods, as deemed most appropriate:
        
        (a) Direct transfer of cryptocurrency to beneficiary-controlled wallets;
        (b) Conversion to traditional currency and distribution of cash proceeds;
        (c) Transfer of physical storage devices containing digital assets;
        (d) Any combination of the above methods as circumstances require."""
        
        story.append(Paragraph(distribution_text, body_style))
        story.append(Spacer(1, 15))
        
        # Tax and Legal Compliance
        story.append(Paragraph("ARTICLE VII - TAX AND REGULATORY COMPLIANCE", heading_style))
        
        tax_text = """I acknowledge that my digital assets may be subject to federal and state income taxes, estate taxes, and capital gains taxes. I authorize my Executor to engage qualified tax professionals and legal advisors to ensure compliance with all applicable tax laws and regulations. My Executor is authorized to make any elections or decisions that may reduce the overall tax burden on my estate and beneficiaries."""
        
        story.append(Paragraph(tax_text, body_style))
        story.append(Spacer(1, 15))
        
        # Fiduciary Protections
        story.append(Paragraph("ARTICLE VIII - FIDUCIARY PROTECTIONS", heading_style))
        
        protection_text = """I acknowledge that digital assets are subject to extreme price volatility and technical risks. My Executor shall not be liable for any decrease in value of digital assets during the administration of my estate, provided that the Executor acts in good faith and with reasonable care. The Executor is authorized to engage technical experts and professional advisors as necessary to properly manage and distribute digital assets, and the costs of such services shall be paid from my estate."""
        
        story.append(Paragraph(protection_text, body_style))
        story.append(Spacer(1, 15))
        
        # Simultaneous Death Clause
        story.append(Paragraph("ARTICLE IX - SIMULTANEOUS DEATH", heading_style))
        
        simultaneous_text = """If any beneficiary dies within thirty (30) days of my death, or if the order of death cannot be determined, such beneficiary shall be deemed to have predeceased me. In such cases, the digital assets designated for that beneficiary shall pass to the contingent beneficiaries as specified herein, or if no contingent beneficiaries are named, shall become part of the residuary estate."""
        
        story.append(Paragraph(simultaneous_text, body_style))
        story.append(Spacer(1, 15))
        
        # No-Contest Clause
        story.append(Paragraph("ARTICLE X - NO-CONTEST PROVISION", heading_style))
        
        no_contest_text = """If any beneficiary contests this Will or challenges any action taken by my Executor regarding the management or distribution of digital assets, and such contest or challenge is unsuccessful, that beneficiary shall forfeit all rights to any distribution under this Will, and their share shall be distributed as if they had predeceased me."""
        
        story.append(Paragraph(no_contest_text, body_style))
        story.append(Spacer(1, 15))
        
        # Residuary Clause
        story.append(Paragraph("ARTICLE XI - RESIDUARY ESTATE", heading_style))
        
        residuary_text = """All the rest, residue, and remainder of my estate, both real and personal, of whatever kind and wherever situated, including any digital assets not specifically disposed of above, I give, devise, and bequeath to my primary beneficiaries in the same proportions as specified for my digital assets."""
        
        story.append(Paragraph(residuary_text, body_style))
        story.append(Spacer(1, 15))
        
        # Miscellaneous Provisions
        story.append(Paragraph("ARTICLE XII - MISCELLANEOUS PROVISIONS", heading_style))
        
        misc_text = """This Will shall be governed by the laws of the state in which I am domiciled at the time of my death. If any provision of this Will is held to be invalid or unenforceable, the remaining provisions shall continue in full force and effect. The masculine gender, wherever used herein, shall include the feminine and neuter genders, and the singular shall include the plural, wherever appropriate."""
        
        story.append(Paragraph(misc_text, body_style))
        story.append(Spacer(1, 30))
        
        # Execution and Signature Section
        story.append(Paragraph("ARTICLE XIII - EXECUTION", heading_style))
        
        execution_text = f"""IN WITNESS WHEREOF, I have hereunto set my hand and seal this _____ day of _____________, 20___, at {personal_info.get('address', {}).get('city', '[CITY]')}, {personal_info.get('address', {}).get('state', '[STATE]')}."""
        
        story.append(Paragraph(execution_text, body_style))
        story.append(Spacer(1, 30))
        
        # Signature lines
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
            ['Date', '    ', 'Date']
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
        
        # Self-Proving Affidavit
        story.append(Paragraph("SELF-PROVING AFFIDAVIT", title_style))
        story.append(Spacer(1, 20))
        
        affidavit_text = f"""STATE OF {personal_info.get('address', {}).get('state', '[STATE]').upper()}
COUNTY OF {personal_info.get('address', {}).get('city', '[COUNTY]').upper()}

We, {testator_name}, the Testator, and the undersigned witnesses, whose names are signed to the attached or foregoing instrument, being first duly sworn, do hereby declare to the undersigned authority that the Testator signed and executed the instrument as the Testator's Last Will and Testament and that the Testator had signed willingly, and that the Testator executed it as a free and voluntary act for the purposes therein expressed, and that each of the witnesses, in the presence and hearing of the Testator, signed the Will as witness and that to the best of their knowledge the Testator was at that time of sound mind and memory.

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
        
        # Footer with generation information
        footer_text = f"This document was generated on {datetime.now().strftime('%B %d, %Y')} using Bitcoin Will Legal Document Generator. This document should be reviewed by a qualified estate planning attorney before execution."
        
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
        print(f"Legal PDF generation error: {e}")
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
    """Download will as comprehensive legal PDF - ENHANCED IMPLEMENTATION"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        print(f"Generating comprehensive legal PDF for will {will_id}")
        
        # Get will data
        will_data = {
            'personal_info': will.get_personal_info(),
            'assets': will.get_bitcoin_assets(),
            'beneficiaries': will.get_beneficiaries(),
            'instructions': will.get_instructions()
        }
        
        # Generate comprehensive legal PDF
        pdf_buffer = generate_legal_will_pdf(will_data, user.email)
        
        if not pdf_buffer:
            return jsonify({'message': 'Failed to generate legal PDF'}), 500
        
        # Return PDF file with legal naming
        safe_title = will.title.replace(' ', '_').replace('/', '_')
        filename = f"Legal_Bitcoin_Will_{safe_title}_{will_id}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Download legal will error: {e}")
        return jsonify({'message': 'Failed to download legal will'}), 500

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

