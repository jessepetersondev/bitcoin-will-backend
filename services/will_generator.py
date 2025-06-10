from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os
from datetime import datetime

class WillGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        # Custom styles for the will document
        self.styles.add(ParagraphStyle(
            name='WillTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='WillBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=0.5*inch,
            rightIndent=0.5*inch
        ))

    def generate_will_pdf(self, will):
        # Create documents directory if it doesn't exist
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'documents')
        os.makedirs(docs_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_will_{will.id}_{timestamp}.pdf"
        filepath = os.path.join(docs_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Title
        story.append(Paragraph("LAST WILL AND TESTAMENT", self.styles['WillTitle']))
        story.append(Paragraph("FOR BITCOIN AND CRYPTOCURRENCY ASSETS", self.styles['WillTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Personal Information Section
        personal_info = will.get_personal_info()
        story.append(Paragraph("I. TESTATOR INFORMATION", self.styles['SectionHeader']))
        
        if personal_info:
            story.append(Paragraph(f"I, <b>{personal_info.get('full_name', '[FULL NAME]')}</b>, of {personal_info.get('address', '[ADDRESS]')}, being of sound mind and disposing memory, do hereby make, publish, and declare this to be my Last Will and Testament for my Bitcoin and cryptocurrency assets, hereby revoking all former wills and codicils by me made.", self.styles['WillBody']))
            
            story.append(Paragraph(f"Date of Birth: {personal_info.get('date_of_birth', '[DATE OF BIRTH]')}", self.styles['WillBody']))
            story.append(Paragraph(f"Social Security Number: {personal_info.get('ssn', '[SSN]')}", self.styles['WillBody']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Bitcoin Assets Section
        bitcoin_assets = will.get_bitcoin_assets()
        story.append(Paragraph("II. BITCOIN AND CRYPTOCURRENCY ASSETS", self.styles['SectionHeader']))
        
        story.append(Paragraph("I hereby declare that I own the following Bitcoin and cryptocurrency assets:", self.styles['WillBody']))
        
        if bitcoin_assets and bitcoin_assets.get('wallets'):
            for i, wallet in enumerate(bitcoin_assets['wallets'], 1):
                story.append(Paragraph(f"<b>Wallet {i}:</b>", self.styles['WillBody']))
                story.append(Paragraph(f"Type: {wallet.get('type', 'Bitcoin')}", self.styles['WillBody']))
                story.append(Paragraph(f"Description: {wallet.get('description', 'N/A')}", self.styles['WillBody']))
                story.append(Paragraph(f"Approximate Value: {wallet.get('value', 'N/A')}", self.styles['WillBody']))
                story.append(Paragraph(f"Wallet Address: {wallet.get('address', '[WALLET ADDRESS]')}", self.styles['WillBody']))
                story.append(Spacer(1, 0.2*inch))
        
        # Private Key Storage Information
        if bitcoin_assets and bitcoin_assets.get('storage_info'):
            storage = bitcoin_assets['storage_info']
            story.append(Paragraph("<b>Private Key Storage Information:</b>", self.styles['WillBody']))
            story.append(Paragraph(f"Storage Method: {storage.get('method', 'Hardware Wallet')}", self.styles['WillBody']))
            story.append(Paragraph(f"Location: {storage.get('location', '[LOCATION]')}", self.styles['WillBody']))
            story.append(Paragraph(f"Additional Details: {storage.get('details', 'N/A')}", self.styles['WillBody']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Beneficiaries Section
        beneficiaries = will.get_beneficiaries()
        story.append(Paragraph("III. BENEFICIARIES", self.styles['SectionHeader']))
        
        story.append(Paragraph("I hereby give, devise, and bequeath my Bitcoin and cryptocurrency assets as follows:", self.styles['WillBody']))
        
        if beneficiaries and beneficiaries.get('primary'):
            for i, beneficiary in enumerate(beneficiaries['primary'], 1):
                story.append(Paragraph(f"<b>Primary Beneficiary {i}:</b>", self.styles['WillBody']))
                story.append(Paragraph(f"Name: {beneficiary.get('name', '[NAME]')}", self.styles['WillBody']))
                story.append(Paragraph(f"Relationship: {beneficiary.get('relationship', '[RELATIONSHIP]')}", self.styles['WillBody']))
                story.append(Paragraph(f"Percentage: {beneficiary.get('percentage', '0')}%", self.styles['WillBody']))
                story.append(Paragraph(f"Contact Information: {beneficiary.get('contact', '[CONTACT INFO]')}", self.styles['WillBody']))
                story.append(Spacer(1, 0.2*inch))
        
        if beneficiaries and beneficiaries.get('contingent'):
            story.append(Paragraph("<b>Contingent Beneficiaries:</b>", self.styles['WillBody']))
            for i, beneficiary in enumerate(beneficiaries['contingent'], 1):
                story.append(Paragraph(f"Name: {beneficiary.get('name', '[NAME]')}, Relationship: {beneficiary.get('relationship', '[RELATIONSHIP]')}, Percentage: {beneficiary.get('percentage', '0')}%", self.styles['WillBody']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Instructions Section
        instructions = will.get_instructions()
        story.append(Paragraph("IV. SPECIAL INSTRUCTIONS FOR BITCOIN ASSETS", self.styles['SectionHeader']))
        
        story.append(Paragraph("The following instructions are provided to assist my beneficiaries in accessing and managing my Bitcoin and cryptocurrency assets:", self.styles['WillBody']))
        
        if instructions:
            if instructions.get('access_instructions'):
                story.append(Paragraph(f"<b>Access Instructions:</b> {instructions['access_instructions']}", self.styles['WillBody']))
            
            if instructions.get('security_notes'):
                story.append(Paragraph(f"<b>Security Notes:</b> {instructions['security_notes']}", self.styles['WillBody']))
            
            if instructions.get('trusted_contacts'):
                story.append(Paragraph("<b>Trusted Technical Contacts:</b>", self.styles['WillBody']))
                for contact in instructions['trusted_contacts']:
                    story.append(Paragraph(f"• {contact.get('name', '[NAME]')} - {contact.get('expertise', '[EXPERTISE]')} - {contact.get('contact', '[CONTACT]')}", self.styles['WillBody']))
        
        # Important Warnings
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("V. IMPORTANT WARNINGS AND DISCLAIMERS", self.styles['SectionHeader']))
        
        warnings = [
            "Bitcoin and cryptocurrency assets are highly volatile and technical in nature.",
            "Private keys must be kept secure and should never be shared or transmitted electronically.",
            "Loss of private keys will result in permanent loss of access to the assets.",
            "Beneficiaries should seek technical assistance from qualified cryptocurrency professionals.",
            "This will should be used in conjunction with a comprehensive estate plan prepared by a qualified attorney.",
            "Tax implications of cryptocurrency inheritance should be discussed with a tax professional."
        ]
        
        for warning in warnings:
            story.append(Paragraph(f"• {warning}", self.styles['WillBody']))
        
        # Executor Section
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("VI. EXECUTOR", self.styles['SectionHeader']))
        
        executor_info = personal_info.get('executor', {}) if personal_info else {}
        story.append(Paragraph(f"I hereby nominate and appoint <b>{executor_info.get('name', '[EXECUTOR NAME]')}</b> as the Executor of this will for my Bitcoin and cryptocurrency assets.", self.styles['WillBody']))
        
        if executor_info.get('contact'):
            story.append(Paragraph(f"Executor Contact Information: {executor_info['contact']}", self.styles['WillBody']))
        
        # Signature Section
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("VII. EXECUTION", self.styles['SectionHeader']))
        
        story.append(Paragraph("IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of _____________, 20___.", self.styles['WillBody']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("_________________________________", self.styles['WillBody']))
        story.append(Paragraph(f"{personal_info.get('full_name', '[TESTATOR NAME]')} (Testator)" if personal_info else "[TESTATOR NAME] (Testator)", self.styles['WillBody']))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Witness Section
        story.append(Paragraph("WITNESSES:", self.styles['SectionHeader']))
        story.append(Paragraph("We, the undersigned, being first duly sworn, declare to the undersigned authority that the testator signed this instrument as the testator's will and that each of us, in the presence of the testator, signed this will as witness to the testator's signing, and that the testator appeared to be of sound mind and under no constraint or undue influence.", self.styles['WillBody']))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Witness 1: _________________________________  Date: ___________", self.styles['WillBody']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Witness 2: _________________________________  Date: ___________", self.styles['WillBody']))
        
        # Notary Section
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("NOTARIZATION", self.styles['SectionHeader']))
        story.append(Paragraph("State of: _________________", self.styles['WillBody']))
        story.append(Paragraph("County of: ________________", self.styles['WillBody']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("On this _____ day of _____________, 20___, before me personally appeared the above-named testator and witnesses, who proved to me on the basis of satisfactory evidence to be the persons whose names are subscribed to the within instrument and acknowledged to me that they executed the same in their authorized capacities.", self.styles['WillBody']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("_________________________________", self.styles['WillBody']))
        story.append(Paragraph("Notary Public", self.styles['WillBody']))
        story.append(Paragraph("My commission expires: ___________", self.styles['WillBody']))
        
        # Build PDF
        doc.build(story)
        
        return filepath

