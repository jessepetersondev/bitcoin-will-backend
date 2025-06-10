from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
from models.user import db, User, Will
import json
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

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

def generate_will_pdf(will_data, user_email):
    """Generate PDF document for will - NEW FUNCTIONALITY"""
    try:
        # Create a BytesIO buffer to hold the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build the PDF content
        story = []
        
        # Title
        story.append(Paragraph("BITCOIN WILL AND TESTAMENT", title_style))
        story.append(Spacer(1, 20))
        
        # Personal Information Section
        if will_data.get('personal_info'):
            personal = will_data['personal_info']
            story.append(Paragraph("PERSONAL INFORMATION", heading_style))
            
            personal_data = [
                ['Full Name:', personal.get('full_name', 'N/A')],
                ['Date of Birth:', personal.get('date_of_birth', 'N/A')],
                ['Address:', personal.get('address', 'N/A')],
                ['Email:', user_email],
                ['Executor Name:', personal.get('executor_name', 'N/A')],
                ['Executor Contact:', personal.get('executor_contact', 'N/A')]
            ]
            
            personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
            personal_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(personal_table)
            story.append(Spacer(1, 20))
        
        # Bitcoin Assets Section
        if will_data.get('assets'):
            assets = will_data['assets']
            story.append(Paragraph("BITCOIN ASSETS", heading_style))
            
            if assets.get('wallets'):
                story.append(Paragraph("Digital Wallets:", styles['Heading3']))
                
                for i, wallet in enumerate(assets['wallets'], 1):
                    wallet_info = [
                        [f'Wallet {i}:', ''],
                        ['Type:', wallet.get('type', 'N/A')],
                        ['Value:', wallet.get('value', 'N/A')],
                        ['Description:', wallet.get('description', 'N/A')],
                        ['Address:', wallet.get('address', 'N/A')]
                    ]
                    
                    wallet_table = Table(wallet_info, colWidths=[1.5*inch, 4.5*inch])
                    wallet_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    
                    story.append(wallet_table)
                    story.append(Spacer(1, 10))
            
            # Storage Information
            if assets.get('storage_method'):
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
                ]))
                
                story.append(storage_table)
            
            story.append(Spacer(1, 20))
        
        # Beneficiaries Section
        if will_data.get('beneficiaries'):
            beneficiaries = will_data['beneficiaries']
            story.append(Paragraph("BENEFICIARIES", heading_style))
            
            if beneficiaries.get('primary'):
                story.append(Paragraph("Primary Beneficiaries:", styles['Heading3']))
                
                for i, beneficiary in enumerate(beneficiaries['primary'], 1):
                    ben_data = [
                        [f'Beneficiary {i}:', ''],
                        ['Name:', beneficiary.get('name', 'N/A')],
                        ['Relationship:', beneficiary.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary.get('percentage', 0)}%"],
                        ['Contact:', beneficiary.get('contact', 'N/A')]
                    ]
                    
                    ben_table = Table(ben_data, colWidths=[1.5*inch, 4.5*inch])
                    ben_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    
                    story.append(ben_table)
                    story.append(Spacer(1, 10))
            
            if beneficiaries.get('contingent'):
                story.append(Paragraph("Contingent Beneficiaries:", styles['Heading3']))
                
                for i, beneficiary in enumerate(beneficiaries['contingent'], 1):
                    ben_data = [
                        [f'Contingent {i}:', ''],
                        ['Name:', beneficiary.get('name', 'N/A')],
                        ['Relationship:', beneficiary.get('relationship', 'N/A')],
                        ['Percentage:', f"{beneficiary.get('percentage', 0)}%"],
                        ['Contact:', beneficiary.get('contact', 'N/A')]
                    ]
                    
                    ben_table = Table(ben_data, colWidths=[1.5*inch, 4.5*inch])
                    ben_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    
                    story.append(ben_table)
                    story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 20))
        
        # Instructions Section
        if will_data.get('instructions'):
            instructions = will_data['instructions']
            story.append(Paragraph("INSTRUCTIONS FOR EXECUTOR", heading_style))
            
            if instructions.get('access_instructions'):
                story.append(Paragraph("Access Instructions:", styles['Heading3']))
                story.append(Paragraph(instructions['access_instructions'], styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('security_notes'):
                story.append(Paragraph("Security Notes:", styles['Heading3']))
                story.append(Paragraph(instructions['security_notes'], styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('trusted_contacts'):
                story.append(Paragraph("Trusted Contacts:", styles['Heading3']))
                
                for contact in instructions['trusted_contacts']:
                    contact_data = [
                        ['Name:', contact.get('name', 'N/A')],
                        ['Contact:', contact.get('contact', 'N/A')]
                    ]
                    
                    contact_table = Table(contact_data, colWidths=[1.5*inch, 4.5*inch])
                    contact_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    
                    story.append(contact_table)
                    story.append(Spacer(1, 8))
        
        # Signature Section
        story.append(Spacer(1, 30))
        story.append(Paragraph("SIGNATURES", heading_style))
        
        signature_data = [
            ['Testator Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Witness 1 Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Witness 2 Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Notary Signature:', '_' * 40, 'Date:', '_' * 20],
            ['Notary Seal:', '', '', '']
        ]
        
        signature_table = Table(signature_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 1.2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(signature_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y')} by Bitcoin Will Service"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None

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
    """Download will as PDF - NEW IMPLEMENTATION"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        will = Will.query.filter_by(id=will_id, user_id=user.id).first()
        
        if not will:
            return jsonify({'message': 'Will not found'}), 404
        
        print(f"Generating PDF for will {will_id}")
        
        # Get will data
        will_data = {
            'personal_info': will.get_personal_info(),
            'assets': will.get_bitcoin_assets(),
            'beneficiaries': will.get_beneficiaries(),
            'instructions': will.get_instructions()
        }
        
        # Generate PDF
        pdf_buffer = generate_will_pdf(will_data, user.email)
        
        if not pdf_buffer:
            return jsonify({'message': 'Failed to generate PDF'}), 500
        
        # Return PDF file
        filename = f"bitcoin_will_{will.title.replace(' ', '_')}_{will_id}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Download will error: {e}")
        return jsonify({'message': 'Failed to download will'}), 500

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

