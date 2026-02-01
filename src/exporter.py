import logging
from fpdf import FPDF

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDF(FPDF):
    def header(self):
        # No header/branding as requested
        pass

    def footer(self):
        # No footer/page numbers as requested
        pass

    def clean_text(self, text):
        """
        Sanitizes text to prevent FPDF encoding errors.
        """
        if not text:
            return ""
        
        # Replace common incompatible characters
        replacements = {
            '\u2022': '-',  # Bullet
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '…': '...',     # Ellipsis
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Final safety net: Strip any remaining non-latin-1 chars
        return text.encode('latin-1', 'replace').decode('latin-1')

    def section_title(self, label):
        """
        Renders a section title with a bottom border.
        """
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        # Title
        self.cell(0, 6, label, ln=True, align='L')
        # Horizontal line (border bottom)
        self.line(self.get_x(), self.get_y(), 200, self.get_y())
        self.ln(2)

    def job_entry(self, role, company, duration, location, points):
        """
        Renders a standard job entry.
        """
        # Line 1: Role (Left) | Duration (Right)
        self.set_font('Arial', 'B', 11)
        self.cell(100, 5, self.clean_text(role), ln=0, align='L')
        
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, self.clean_text(duration), ln=1, align='R')
        
        # Line 2: Company (Left) | Location (Right)
        # Only print if company or location exists
        if company or location:
            self.set_font('Arial', 'I', 11)
            self.cell(100, 5, self.clean_text(company), ln=0, align='L')
            
            self.set_font('Arial', 'I', 10)
            self.cell(0, 5, self.clean_text(location), ln=1, align='R')
        
        # Bullets
        self.set_font('Arial', '', 10)
        if points:
            for point in points:
                # Add a dash and indent
                clean_point = "- " + self.clean_text(point)
                self.set_x(15) # Indent
                self.multi_cell(175, 5, clean_point)
        
        self.ln(3) # Spacing after entry

    def education_entry(self, school, degree, duration, location):
        """
        Renders an education entry.
        """
        # Line 1: School (Left) | Duration (Right)
        self.set_font('Arial', 'B', 11)
        self.cell(120, 5, self.clean_text(school), ln=0, align='L')
        
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, self.clean_text(duration), ln=1, align='R')
        
        # Line 2: Degree (Left) | Location (Right)
        self.set_font('Arial', '', 10)
        self.cell(120, 5, self.clean_text(degree), ln=0, align='L')
        
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, self.clean_text(location), ln=1, align='R')
        
        self.ln(3)

def save_as_pdf(resume_data):
    """
    Converts structured resume data to PDF bytes.
    """
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- Personal Info Section ---
        personal_info = resume_data.get('personal_info', {})
        
        # Name
        name = personal_info.get('name', 'Resume')
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, pdf.clean_text(name), ln=True, align='C')
        
        # Contact Info - Robust filtering
        contact_items = [
            personal_info.get('phone'),
            personal_info.get('email'),
            personal_info.get('linkedin'),
            personal_info.get('github'),
            personal_info.get('location')
        ]
        # Filter out None and empty strings/spaces
        valid_contact_items = [item for item in contact_items if item and item.strip()]
        
        if valid_contact_items:
            contact_line = ' | '.join(valid_contact_items)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 5, pdf.clean_text(contact_line), ln=True, align='C')
        
        pdf.ln(5)
        
        # --- Skills Section ---
        skills = resume_data.get('skills', [])
        if skills:
            pdf.section_title('SKILLS')
            skills_text = ', '.join(skills)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, pdf.clean_text(skills_text))
        
        # --- Experience Section ---
        experience = resume_data.get('experience', [])
        if experience:
            pdf.section_title('EXPERIENCE')
            for exp in experience:
                pdf.job_entry(
                    role=exp.get('role', ''),
                    company=exp.get('company', ''),
                    duration=exp.get('duration', ''),
                    location=exp.get('location', ''),
                    points=exp.get('points', [])
                )
        
        # --- Projects Section ---
        projects = resume_data.get('projects', [])
        if projects:
            pdf.section_title('PROJECTS')
            for proj in projects:
                # Reuse job_entry for projects:
                # Title -> Role (Bold)
                # Role -> Company (Italic)
                pdf.job_entry(
                    role=proj.get('title', ''),
                    company=proj.get('role', ''),
                    duration=proj.get('duration', ''),
                    location='', # Usually no location for projects
                    points=proj.get('points', [])
                )
        
        # --- Education Section ---
        education = resume_data.get('education', [])
        if education:
            pdf.section_title('EDUCATION')
            for edu in education:
                pdf.education_entry(
                    school=edu.get('school', ''),
                    degree=edu.get('degree', ''),
                    duration=edu.get('duration', ''),
                    location=edu.get('location', '')
                )
        
        return bytes(pdf.output())
        
    except Exception as e:
        logger.error(f"PDF Generation failed: {str(e)}")
        err_pdf = FPDF()
        err_pdf.add_page()
        err_pdf.set_font('Arial', '', 12)
        err_pdf.multi_cell(0, 10, f"Error generating PDF: {str(e)}")
        return bytes(err_pdf.output())