import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts raw text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

if __name__ == "__main__":
    # This block only runs when we execute this file directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    resume_path = os.path.join(project_root, "my_resume.pdf")

    print(f"🔍 Reading resume from: {resume_path}")
    
    resume_text = extract_text_from_pdf(resume_path)
    
    if resume_text:
        print("\n✅ SUCCESS! Extracted Text Preview:")
        print("-" * 40)
        print(resume_text[:500])  # Print first 500 characters
        print("-" * 40)
    else:
        print("❌ Failed to extract text.")