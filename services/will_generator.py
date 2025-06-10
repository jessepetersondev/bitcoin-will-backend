import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import json

class WillGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
    def generate_will_pdf(self, will):
        """Generate a comprehensive Bitcoin will PDF document"""
        
        # Create documents directory if it doesn't exist
        docs_dir = os.path.join(os.getcwd(), 'documents')
        os.makedirs(docs_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bitcoin_will_{will.id}_{timestamp}.pdf'
        filepath = os.path.join(docs_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=1*inch)
        story = []
        
        # Title
        story.append(Paragraph("LAST WILL AND TESTAMENT", self.title_style))
        story.append(Paragraph("FOR BITCOIN AND CRYPTOCURRENCY ASSETS", self.title_style))
        story.append(Spacer(1, 20))
        
        # Personal Information
        personal_info = will.get_personal_info()
        if personal_info:
            story.append(Paragraph("I. PERSONAL INFORMATION", self.heading_style))
            
            story.append(Paragraph(f"<b>Full Name:</b> {personal_info.get('full_name', 'N/A')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Date of Birth:</b> {personal_info.get('date_of_birth', 'N/A')}", self.styles['Normal']))
            
            address = personal_info.get('address', {})
            address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}, {address.get('country', '')}"
            story.append(Paragraph(f"<b>Address:</b> {address_str}", self.styles['Normal']))
            
            story.append(Paragraph(f"<b>Phone:</b> {personal_info.get('phone', 'N/A')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Email:</b> {personal_info.get('email', 'N/A')}", self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Declaration
        story.append(Paragraph("II. DECLARATION", self.heading_style))
        story.append(Paragraph(
            "I, being of sound mind and disposing memory, do hereby make, publish, and declare this to be my Last Will and Testament for my Bitcoin and cryptocurrency assets, hereby revoking any and all former wills and codicils relating to digital assets made by me.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Bitcoin Assets
        bitcoin_assets = will.get_bitcoin_assets()
        if bitcoin_assets:
            story.append(Paragraph("III. BITCOIN AND CRYPTOCURRENCY ASSETS", self.heading_style))
            
            # Wallets
            wallets = bitcoin_assets.get('wallets', [])
            if wallets:
                story.append(Paragraph("<b>A. Bitcoin Wallets:</b>", self.styles['Heading3']))
                for i, wallet in enumerate(wallets, 1):
                    story.append(Paragraph(f"<b>Wallet {i}:</b>", self.styles['Normal']))
                    story.append(Paragraph(f"Name: {wallet.get('name', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Type: {wallet.get('type', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Description: {wallet.get('description', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Access Method: {wallet.get('access_method', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Seed Phrase Location: {wallet.get('seed_phrase_location', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Private Key Location: {wallet.get('private_key_location', 'N/A')}", self.styles['Normal']))
                    if wallet.get('additional_notes'):
                        story.append(Paragraph(f"Additional Notes: {wallet['additional_notes']}", self.styles['Normal']))
                    story.append(Spacer(1, 10))
            
            # Exchanges
            exchanges = bitcoin_assets.get('exchanges', [])
            if exchanges:
                story.append(Paragraph("<b>B. Cryptocurrency Exchanges:</b>", self.styles['Heading3']))
                for i, exchange in enumerate(exchanges, 1):
                    story.append(Paragraph(f"<b>Exchange {i}:</b>", self.styles['Normal']))
                    story.append(Paragraph(f"Name: {exchange.get('name', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Username: {exchange.get('username', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Email: {exchange.get('email', 'N/A')}", self.styles['Normal']))
                    story.append(Paragraph(f"Two-Factor Backup: {exchange.get('two_factor_backup', 'N/A')}", self.styles['Normal']))
                    if exchange.get('additional_notes'):
                        story.append(Paragraph(f"Additional Notes: {exchange['additional_notes']}", self.styles['Normal']))
                    story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 20))
        
        # Beneficiaries
        beneficiaries = will.get_beneficiaries()
        if beneficiaries:
            story.append(Paragraph("IV. BENEFICIARIES AND DISTRIBUTION", self.heading_style))
            
            for i, beneficiary in enumerate(beneficiaries, 1):
                story.append(Paragraph(f"<b>Beneficiary {i}:</b>", self.styles['Heading3']))
                story.append(Paragraph(f"Name: {beneficiary.get('name', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Relationship: {beneficiary.get('relationship', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Percentage of Assets: {beneficiary.get('percentage', 0)}%", self.styles['Normal']))
                
                address = beneficiary.get('address', {})
                if any(address.values()):
                    address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip_code', '')}, {address.get('country', '')}"
                    story.append(Paragraph(f"Address: {address_str}", self.styles['Normal']))
                
                story.append(Paragraph(f"Phone: {beneficiary.get('phone', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Email: {beneficiary.get('email', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Bitcoin Address: {beneficiary.get('bitcoin_address', 'N/A')}", self.styles['Normal']))
                
                backup_contact = beneficiary.get('backup_contact', {})
                if backup_contact.get('name'):
                    story.append(Paragraph(f"Backup Contact: {backup_contact.get('name', 'N/A')} - {backup_contact.get('phone', 'N/A')}", self.styles['Normal']))
                
                story.append(Spacer(1, 15))
        
        # Instructions
        instructions = will.get_instructions()
        if instructions:
            story.append(Paragraph("V. EXECUTOR AND INSTRUCTIONS", self.heading_style))
            
            executor = instructions.get('executor', {})
            if executor.get('name'):
                story.append(Paragraph("<b>Executor:</b>", self.styles['Heading3']))
                story.append(Paragraph(f"Name: {executor.get('name', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Relationship: {executor.get('relationship', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Phone: {executor.get('phone', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Email: {executor.get('email', 'N/A')}", self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('distribution_instructions'):
                story.append(Paragraph("<b>Distribution Instructions:</b>", self.styles['Heading3']))
                story.append(Paragraph(instructions['distribution_instructions'], self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            if instructions.get('technical_instructions'):
                story.append(Paragraph("<b>Technical Instructions:</b>", self.styles['Heading3']))
                story.append(Paragraph(instructions['technical_instructions'], self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Emergency Contacts
            emergency_contacts = instructions.get('emergency_contacts', [])
            if emergency_contacts:
                story.append(Paragraph("<b>Emergency Contacts:</b>", self.styles['Heading3']))
                for contact in emergency_contacts:
                    if contact.get('name'):
                        story.append(Paragraph(f"{contact.get('name', 'N/A')} ({contact.get('relationship', 'N/A')}) - {contact.get('phone', 'N/A')}", self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Lawyer Contact
            lawyer = instructions.get('lawyer_contact', {})
            if lawyer.get('name'):
                story.append(Paragraph("<b>Legal Counsel:</b>", self.styles['Heading3']))
                story.append(Paragraph(f"Name: {lawyer.get('name', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Firm: {lawyer.get('firm', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Phone: {lawyer.get('phone', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"Email: {lawyer.get('email', 'N/A')}", self.styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Legal Disclaimers
        story.append(Spacer(1, 30))
        story.append(Paragraph("VI. LEGAL DISCLAIMERS AND NOTES", self.heading_style))
        story.append(Paragraph(
            "This document serves as a comprehensive record of Bitcoin and cryptocurrency assets for estate planning purposes. "
            "It is strongly recommended that this document be reviewed and properly executed with the assistance of qualified legal counsel "
            "to ensure compliance with local laws and regulations.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(
            "<b>IMPORTANT:</b> This document contains sensitive information about cryptocurrency assets. "
            "Store this document securely and ensure that trusted individuals know of its existence and location.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 30))
        
        # Signature Section
        story.append(Paragraph("VII. EXECUTION", self.heading_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 40))
        
        # Signature lines
        signature_data = [
            ['Testator Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Print Name:', '_' * 40, '', ''],
            ['', '', '', ''],
            ['Witness 1 Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Print Name:', '_' * 40, '', ''],
            ['', '', '', ''],
            ['Witness 2 Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Print Name:', '_' * 40, '', ''],
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 2.5*inch, 0.8*inch, 1.5*inch])
        signature_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        
        return filepath

