import logging
from fpdf import FPDF

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDF(FPDF):
    def header(self):
        # Font: Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Resume Tailor AI Results', ln=True, align='C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', align='C')

    def clean_text(self, text):
        """
        Sanitizes text to prevent FPDF encoding errors.
        Replaces fancy characters with standard ASCII equivalents.
        """
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

def save_as_pdf(markdown_content):
    """
    Converts markdown content to PDF bytes.
    """
    try:
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Process lines
        lines = markdown_content.split('\n')
        
        for line in lines:
            safe_line = pdf.clean_text(line).strip()
            
            if not safe_line:
                pdf.ln(5) # Empty line spacing
                continue
                
            # Formatting logic
            if safe_line.startswith('#'):
                # Header Style
                pdf.set_font('Arial', 'B', 14)
                # Remove the # characters
                clean_header = safe_line.replace('#', '').strip()
                pdf.set_x(10) # FORCE RESET to left margin
                pdf.multi_cell(0, 10, clean_header)
                
            elif safe_line.startswith('-') or safe_line.startswith('*'):
                # List Item Style
                pdf.set_font('Arial', '', 11)
                pdf.set_x(15) # Slight Indent (15mm)
                # w=175 ensures it fits within A4 width (210mm) - margins
                pdf.multi_cell(175, 6, safe_line)
                
            else:
                # Standard Text
                pdf.set_font('Arial', '', 11)
                pdf.set_x(10) # FORCE RESET to left margin
                pdf.multi_cell(0, 6, safe_line)
        
        # FIX: Convert bytearray to bytes
        return bytes(pdf.output())
        
    except Exception as e:
        logger.error(f"PDF Generation failed: {str(e)}")
        # Return a simple error PDF so the app doesn't crash
        err_pdf = FPDF()
        err_pdf.add_page()
        err_pdf.set_font('Arial', '', 12)
        err_pdf.multi_cell(0, 10, f"Error generating PDF: {str(e)}")
        # FIX: Convert bytearray to bytes
        return bytes(err_pdf.output())