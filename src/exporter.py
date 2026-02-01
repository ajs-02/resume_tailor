import logging

from fpdf import FPDF

from config import PDF_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        pass

    def clean_text(self, text):
        """Sanitize text to prevent FPDF encoding errors."""
        if not text:
            return ""

        replacements = {
            '\u2022': '-',
            '\u2013': '-',
            '\u2014': '-',
            '\u2018': "'",
            '\u2019': "'",
            '\u201c': '"',
            '\u201d': '"',
            '…': '...',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        encoding = PDF_CONFIG["encoding"]
        return text.encode(encoding, 'replace').decode(encoding)

    def section_title(self, label):
        """Render section title with bottom border."""
        font = PDF_CONFIG["font_family"]
        size = PDF_CONFIG["font_sizes"]["section_title"]
        self.ln(5)
        self.set_font(font, 'B', size)
        self.cell(0, 6, label, ln=True, align='L')
        self.line(self.get_x(), self.get_y(), 200, self.get_y())
        self.ln(2)

    def job_entry(self, role, company, duration, location, points):
        """Render job or project entry."""
        font = PDF_CONFIG["font_family"]
        size_title = PDF_CONFIG["font_sizes"]["job_title"]
        size_body = PDF_CONFIG["font_sizes"]["body"]

        self.set_font(font, 'B', size_title)
        self.cell(100, 5, self.clean_text(role), ln=0, align='L')

        self.set_font(font, 'I', size_body)
        self.cell(0, 5, self.clean_text(duration), ln=1, align='R')

        if company or location:
            self.set_font(font, 'I', size_title)
            self.cell(100, 5, self.clean_text(company), ln=0, align='L')

            self.set_font(font, 'I', size_body)
            self.cell(0, 5, self.clean_text(location), ln=1, align='R')

        self.set_font(font, '', size_body)
        if points:
            for point in points:
                clean_point = "- " + self.clean_text(point)
                self.set_x(15)
                self.multi_cell(175, 5, clean_point)

        self.ln(3)

    def education_entry(self, school, degree, duration, location):
        """Render education entry."""
        font = PDF_CONFIG["font_family"]
        size_title = PDF_CONFIG["font_sizes"]["job_title"]
        size_body = PDF_CONFIG["font_sizes"]["body"]

        self.set_font(font, 'B', size_title)
        self.cell(120, 5, self.clean_text(school), ln=0, align='L')

        self.set_font(font, 'I', size_body)
        self.cell(0, 5, self.clean_text(duration), ln=1, align='R')

        self.set_font(font, '', size_body)
        self.cell(120, 5, self.clean_text(degree), ln=0, align='L')

        self.set_font(font, 'I', size_body)
        self.cell(0, 5, self.clean_text(location), ln=1, align='R')

        self.ln(3)

def save_as_pdf(resume_data):
    """Convert structured resume data to PDF bytes.

    Args:
        resume_data: Dictionary containing resume sections

    Returns:
        PDF file as bytes
    """
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(
            auto=PDF_CONFIG["auto_page_break"],
            margin=PDF_CONFIG["margin"]
        )

        personal_info = resume_data.get('personal_info', {})

        name = personal_info.get('name', 'Resume')
        font = PDF_CONFIG["font_family"]
        size_name = PDF_CONFIG["font_sizes"]["name"]
        pdf.set_font(font, 'B', size_name)
        pdf.cell(0, 10, pdf.clean_text(name), ln=True, align='C')

        contact_items = [
            personal_info.get('phone'),
            personal_info.get('email'),
            personal_info.get('linkedin'),
            personal_info.get('github'),
            personal_info.get('location')
        ]
        valid_contact_items = [item for item in contact_items if item and item.strip()]

        if valid_contact_items:
            contact_line = ' | '.join(valid_contact_items)
            size_body = PDF_CONFIG["font_sizes"]["body"]
            pdf.set_font(font, '', size_body)
            pdf.cell(0, 5, pdf.clean_text(contact_line), ln=True, align='C')

        pdf.ln(5)

        skills = resume_data.get('skills', [])
        if skills:
            pdf.section_title('SKILLS')
            skills_text = ', '.join(skills)
            pdf.set_font(font, '', size_body)
            pdf.multi_cell(0, 5, pdf.clean_text(skills_text))

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

        projects = resume_data.get('projects', [])
        if projects:
            pdf.section_title('PROJECTS')
            for proj in projects:
                pdf.job_entry(
                    role=proj.get('title', ''),
                    company=proj.get('role', ''),
                    duration=proj.get('duration', ''),
                    location='',
                    points=proj.get('points', [])
                )

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
        font = PDF_CONFIG["font_family"]
        size_error = PDF_CONFIG["font_sizes"]["error"]
        err_pdf.set_font(font, '', size_error)
        err_pdf.multi_cell(0, 10, f"Error generating PDF: {str(e)}")
        return bytes(err_pdf.output())