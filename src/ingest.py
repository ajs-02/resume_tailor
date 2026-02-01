import os

from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    """Extract raw text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text string or None on error
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    resume_path = os.path.join(project_root, "my_resume.pdf")

    print(f"[INFO] Reading resume from: {resume_path}")

    resume_text = extract_text_from_pdf(resume_path)

    if resume_text:
        print("\n[INFO] SUCCESS! Extracted Text Preview:")
        print("-" * 40)
        print(resume_text[:500])
        print("-" * 40)
    else:
        print("[ERROR] Failed to extract text.")