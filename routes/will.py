from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
import json
import tempfile
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import io

# Session-only will routes - NO DATABASE STORAGE for Bitcoin data
will_bp = Blueprint('will', __name__)

@will_bp.route('/generate-session', methods=['POST', 'OPTIONS'])
@cross_origin()
def generate_session_will():
    """
    Generate will PDF from session data without storing any Bitcoin information
    This is the main endpoint for secure, session-only will creation
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Get will data from request (not from database)
        will_data = request.get_json()
        
        if not will_data:
            return jsonify({'error': 'No will data provided'}), 400
        
        print(f"Generating session-only will PDF (no storage)")
        
        # Generate PDF from session data
        pdf_buffer = generate_comprehensive_legal_pdf(will_data)
        
        if not pdf_buffer:
            return jsonify({'error': 'Failed to generate PDF'}), 500
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_buffer.getvalue())
        temp_file.close()
        
        # Generate filename
        personal_info = will_data.get('personal_info', {})
        full_name = personal_info.get('full_name', 'Bitcoin_Will')
        safe_name = ''.join(c for c in full_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"Bitcoin_Will_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        def cleanup_temp_file():
            """Clean up temporary file after sending"""
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
        # Send file and schedule cleanup
        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # Schedule cleanup after response
        response.call_on_close(cleanup_temp_file)
        
        print(f"Session-only will PDF generated successfully: {filename}")
        return response
        
    except Exception as e:
        print(f"Session will generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate will PDF'}), 500

def generate_comprehensive_legal_pdf(will_data):
    """
    Generate comprehensive legal Bitcoin will PDF with all necessary clauses
    Enhanced version with proper legal structure and Bitcoin-specific provisions
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles for legal document
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
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
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leading=14
        )
        
        # Build document content
        story = []
        
        # Document title
        story.append(Paragraph("LAST WILL AND TESTAMENT", title_style))
        story.append(Paragraph("BITCOIN AND CRYPTOCURRENCY ESTATE PLANNING DOCUMENT", heading_style))
        story.append(Spacer(1, 20))
        
        # Personal information
        personal_info = will_data.get('personal_info', {})
        full_name = personal_info.get('full_name', 'Not Specified')
        
        story.append(Paragraph(f"I, <b>{full_name}</b>, being of sound mind and disposing memory, do hereby make, publish, and declare this to be my Last Will and Testament, hereby revoking all former wills and codicils made by me.", body_style))
        story.append(Spacer(1, 20))
        
        # Article I - Declaration
        story.append(Paragraph("ARTICLE I<br/>DECLARATION", heading_style))
        
        address = personal_info.get('address', {})
        address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}"
        
        story.append(Paragraph(f"I am a resident of {address_str}. I am of sound mind and under no constraint or undue influence. I am over the age of eighteen (18) years.", body_style))
        
        if personal_info.get('date_of_birth'):
            story.append(Paragraph(f"My date of birth is {personal_info.get('date_of_birth')}.", body_style))
        
        story.append(Spacer(1, 15))
        
        # Article II - Revocation
        story.append(Paragraph("ARTICLE II<br/>REVOCATION OF PRIOR WILLS", heading_style))
        story.append(Paragraph("I hereby revoke all wills and codicils previously made by me.", body_style))
        story.append(Spacer(1, 15))
        
        # Article III - Executor
        story.append(Paragraph("ARTICLE III<br/>APPOINTMENT OF EXECUTOR", heading_style))
        
        executor_name = personal_info.get('executor_name', 'Not Specified')
        executor_contact = personal_info.get('executor_contact', 'Not Specified')
        
        story.append(Paragraph(f"I hereby nominate and appoint <b>{executor_name}</b> (Contact: {executor_contact}) as the Executor of this Will. If {executor_name} is unable or unwilling to serve, I nominate [ALTERNATE EXECUTOR TO BE SPECIFIED] as alternate Executor.", body_style))
        
        story.append(Paragraph("I grant my Executor full power and authority to administer my estate, including but not limited to the power to:", body_style))
        
        executor_powers = [
            "Access, manage, and distribute all digital assets including Bitcoin and cryptocurrency",
            "Engage cryptocurrency experts and technical advisors as needed",
            "Convert digital assets to fiat currency if necessary for estate administration",
            "Pay all debts, taxes, and administration expenses",
            "Distribute assets to beneficiaries according to this Will",
            "Take any action necessary for proper estate administration"
        ]
        
        for power in executor_powers:
            story.append(Paragraph(f"• {power}", body_style))
        
        story.append(Spacer(1, 15))
        
        # Article IV - Bitcoin and Cryptocurrency Assets
        story.append(Paragraph("ARTICLE IV<br/>BITCOIN AND CRYPTOCURRENCY ASSETS", heading_style))
        
        bitcoin_assets = will_data.get('bitcoin_assets', {})
        
        story.append(Paragraph("I hereby give, devise, and bequeath all of my Bitcoin, cryptocurrency, and digital assets as follows:", body_style))
        
        # Storage information
        if bitcoin_assets.get('storage_method'):
            story.append(Paragraph(f"<b>Storage Method:</b> {bitcoin_assets.get('storage_method')}", body_style))
        if bitcoin_assets.get('storage_location'):
            story.append(Paragraph(f"<b>Storage Location:</b> {bitcoin_assets.get('storage_location')}", body_style))
        if bitcoin_assets.get('storage_details'):
            story.append(Paragraph(f"<b>Storage Details:</b> {bitcoin_assets.get('storage_details')}", body_style))
        
        story.append(Spacer(1, 10))
        
        # Wallets table
        wallets = bitcoin_assets.get('wallets', [])
        if wallets:
            story.append(Paragraph("<b>BITCOIN WALLETS AND DIGITAL ASSETS:</b>", body_style))
            story.append(Spacer(1, 10))
            
            wallet_data = [['Wallet Name', 'Type', 'Description', 'Access Method']]
            for wallet in wallets:
                wallet_data.append([
                    wallet.get('name', 'N/A'),
                    wallet.get('type', 'N/A'),
                    wallet.get('description', 'N/A'),
                    wallet.get('access_method', 'See separate instructions')
                ])
            
            wallet_table = Table(wallet_data, colWidths=[1.5*inch, 1*inch, 2*inch, 1.5*inch])
            wallet_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(wallet_table)
            story.append(Spacer(1, 15))
        
        # Exchange accounts
        exchanges = bitcoin_assets.get('exchanges', [])
        if exchanges:
            story.append(Paragraph("<b>CRYPTOCURRENCY EXCHANGE ACCOUNTS:</b>", body_style))
            story.append(Spacer(1, 10))
            
            exchange_data = [['Exchange Name', 'Username/Account', 'Email', '2FA Backup Location']]
            for exchange in exchanges:
                exchange_data.append([
                    exchange.get('name', 'N/A'),
                    exchange.get('username', 'N/A'),
                    exchange.get('email', 'N/A'),
                    exchange.get('two_factor_backup', 'See instructions')
                ])
            
            exchange_table = Table(exchange_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            exchange_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(exchange_table)
            story.append(Spacer(1, 15))
        
        # Article V - Beneficiaries
        story.append(Paragraph("ARTICLE V<br/>BENEFICIARIES AND DISTRIBUTION", heading_style))
        
        beneficiaries = will_data.get('beneficiaries', {})
        primary_beneficiaries = beneficiaries.get('primary', [])
        
        if primary_beneficiaries:
            story.append(Paragraph("<b>PRIMARY BENEFICIARIES:</b>", body_style))
            story.append(Paragraph("I give, devise, and bequeath my Bitcoin and cryptocurrency assets to the following primary beneficiaries:", body_style))
            story.append(Spacer(1, 10))
            
            beneficiary_data = [['Name', 'Relationship', 'Percentage', 'Contact Information']]
            for beneficiary in primary_beneficiaries:
                contact_info = f"Phone: {beneficiary.get('phone', 'N/A')}\nEmail: {beneficiary.get('email', 'N/A')}"
                if beneficiary.get('address', {}).get('street'):
                    addr = beneficiary.get('address', {})
                    contact_info += f"\nAddress: {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip_code', '')}"
                
                beneficiary_data.append([
                    beneficiary.get('name', 'N/A'),
                    beneficiary.get('relationship', 'N/A'),
                    f"{beneficiary.get('percentage', '0')}%",
                    contact_info
                ])
            
            beneficiary_table = Table(beneficiary_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 2.7*inch])
            beneficiary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(beneficiary_table)
            story.append(Spacer(1, 15))
        
        # Contingent beneficiaries
        contingent_beneficiaries = beneficiaries.get('contingent', [])
        if contingent_beneficiaries:
            story.append(Paragraph("<b>CONTINGENT BENEFICIARIES:</b>", body_style))
            story.append(Paragraph("If any primary beneficiary predeceases me or is unable to inherit, their share shall pass to the following contingent beneficiaries:", body_style))
            story.append(Spacer(1, 10))
            
            contingent_data = [['Name', 'Relationship', 'Percentage', 'Contact Information']]
            for beneficiary in contingent_beneficiaries:
                contact_info = f"Phone: {beneficiary.get('phone', 'N/A')}\nEmail: {beneficiary.get('email', 'N/A')}"
                if beneficiary.get('address', {}).get('street'):
                    addr = beneficiary.get('address', {})
                    contact_info += f"\nAddress: {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip_code', '')}"
                
                contingent_data.append([
                    beneficiary.get('name', 'N/A'),
                    beneficiary.get('relationship', 'N/A'),
                    f"{beneficiary.get('percentage', '0')}%",
                    contact_info
                ])
            
            contingent_table = Table(contingent_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 2.7*inch])
            contingent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(contingent_table)
            story.append(Spacer(1, 15))
        
        # Article VI - Access Instructions
        story.append(Paragraph("ARTICLE VI<br/>ACCESS INSTRUCTIONS AND SECURITY", heading_style))
        
        instructions = will_data.get('instructions', {})
        
        if instructions.get('access_instructions'):
            story.append(Paragraph("<b>ACCESS INSTRUCTIONS:</b>", body_style))
            story.append(Paragraph(instructions.get('access_instructions'), body_style))
            story.append(Spacer(1, 10))
        
        if instructions.get('security_notes'):
            story.append(Paragraph("<b>SECURITY NOTES:</b>", body_style))
            story.append(Paragraph(instructions.get('security_notes'), body_style))
            story.append(Spacer(1, 10))
        
        # Trusted contacts
        trusted_contacts = instructions.get('trusted_contacts', [])
        if trusted_contacts:
            story.append(Paragraph("<b>TRUSTED CONTACTS:</b>", body_style))
            story.append(Paragraph("The following individuals may be contacted for assistance with digital asset recovery:", body_style))
            story.append(Spacer(1, 10))
            
            contact_data = [['Name', 'Relationship', 'Contact Information', 'Role']]
            for contact in trusted_contacts:
                contact_data.append([
                    contact.get('name', 'N/A'),
                    contact.get('relationship', 'N/A'),
                    contact.get('contact', 'N/A'),
                    contact.get('role', 'Technical Advisor')
                ])
            
            contact_table = Table(contact_data, colWidths=[1.5*inch, 1*inch, 2*inch, 1.5*inch])
            contact_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(contact_table)
            story.append(Spacer(1, 15))
        
        # Article VII - Legal Provisions
        story.append(Paragraph("ARTICLE VII<br/>LEGAL PROVISIONS", heading_style))
        
        legal_provisions = [
            "If any beneficiary contests this Will or any provision hereof, that beneficiary shall forfeit any interest in my estate.",
            "This Will shall be governed by the laws of the state in which I reside at the time of my death.",
            "If any provision of this Will is deemed invalid, the remaining provisions shall remain in full force and effect.",
            "My Executor is authorized to engage cryptocurrency experts, tax professionals, and legal counsel as needed for proper administration of digital assets.",
            "All taxes, debts, and administration expenses shall be paid from the estate before distribution to beneficiaries."
        ]
        
        for provision in legal_provisions:
            story.append(Paragraph(f"• {provision}", body_style))
        
        story.append(Spacer(1, 20))
        
        # Article VIII - Execution
        story.append(Paragraph("ARTICLE VIII<br/>EXECUTION", heading_style))
        
        story.append(Paragraph("IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of _____________, 20___, in the presence of the witnesses whose signatures appear below.", body_style))
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_data = [
            ['', ''],
            ['_' * 40, '_' * 40],
            [f'{full_name}', 'Date'],
            ['Testator', '']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 2), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
        ]))
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # Witness section
        story.append(Paragraph("WITNESSES:", body_style))
        story.append(Paragraph("We, the undersigned witnesses, each do hereby declare in the presence of the aforesaid Testator that the Testator signed and executed this instrument as the Testator's Last Will and Testament and that each of us, in the hearing and sight of the Testator, hereby signs this Will as witness to the Testator's signing, and that to the best of our knowledge the Testator is eighteen years of age or over, of sound mind and under no constraint or undue influence.", body_style))
        story.append(Spacer(1, 20))
        
        witness_data = [
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
        
        witness_table = Table(witness_data, colWidths=[3*inch, 3*inch])
        witness_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
            ('TOPPADDING', (0, 4), (-1, 4), 10),
            ('TOPPADDING', (0, 7), (-1, 7), 10),
            ('TOPPADDING', (0, 10), (-1, 10), 10),
        ]))
        story.append(witness_table)
        story.append(Spacer(1, 30))
        
        # Legal disclaimer
        story.append(Paragraph("LEGAL DISCLAIMER", heading_style))
        story.append(Paragraph("This document has been generated using Bitcoin Will estate planning software. While this document includes standard legal provisions for wills and cryptocurrency-specific clauses, it is strongly recommended that you consult with a qualified estate planning attorney in your jurisdiction to ensure this will meets all local legal requirements and properly addresses your specific circumstances. Laws regarding wills and digital assets vary by jurisdiction and are subject to change.", body_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        return None

# Health check endpoint
@will_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for session-only will service"""
    return jsonify({
        'status': 'healthy',
        'service': 'session-only-will-generator',
        'security': 'no-bitcoin-data-storage',
        'timestamp': datetime.now().isoformat()
    }), 200

# Remove all database-related will endpoints for security
# No more /will/create, /will/list, /will/edit, /will/delete endpoints
# Only session-based PDF generation remains

