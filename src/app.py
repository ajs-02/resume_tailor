import os
import sys
import asyncio
import tempfile
import streamlit as st
from dotenv import load_dotenv

from ingest import extract_text_from_pdf
from scraper import JobScraper
from tailor import ResumeTailor
from exporter import save_as_pdf


def setup_encoding():
    """Ensure UTF-8 encoding for Windows."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')


def get_api_key(user_provided_key: str) -> str:
    """
    Get API key from user input or environment.
    
    Args:
        user_provided_key: API key provided by user in UI
        
    Returns:
        str: API key to use
        
    Raises:
        ValueError: If no API key is found
    """
    if user_provided_key and user_provided_key.strip():
        return user_provided_key.strip()
    
    load_dotenv()
    env_key = os.getenv("GEMINI_API_KEY")
    
    if env_key:
        return env_key
    
    raise ValueError("No API key provided. Please enter your Gemini API key or set GEMINI_API_KEY in .env file.")


async def scrape_job_async(url: str) -> str:
    """
    Async wrapper for job scraping.
    
    Args:
        url: Job posting URL
        
    Returns:
        str: Scraped job description in markdown
    """
    async with JobScraper() as scraper:
        return await scraper.scrape_job(url)


def process_resume_tailoring(resume_file, job_url: str, api_key: str):
    """
    Main processing function that orchestrates the resume tailoring workflow.
    
    Args:
        resume_file: Uploaded PDF file
        job_url: Job posting URL
        api_key: Gemini API key
        
    Returns:
        str: Tailored resume text
    """
    # Step 1: Extract text from PDF
    with st.status("Step 1: Scanning resume...", expanded=True) as status:
        st.write("Reading PDF file...")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(resume_file.read())
            tmp_path = tmp_file.name
        
        try:
            resume_text = extract_text_from_pdf(tmp_path)
            
            if not resume_text or not resume_text.strip():
                raise ValueError("Failed to extract text from PDF. The file may be empty or corrupted.")
            
            st.write(f"Successfully extracted {len(resume_text)} characters from resume")
            status.update(label="Step 1: Resume scanned successfully", state="complete")
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    # Step 2: Scrape job description
    with st.status("Step 2: Scraping job description...", expanded=True) as status:
        st.write(f"Fetching content from: {job_url}")
        
        try:
            # Fix for Windows + Streamlit + Playwright
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # Run async scraper in sync context
            job_description = asyncio.run(scrape_job_async(job_url))
            
            if not job_description or not job_description.strip():
                raise ValueError("Failed to scrape job description. The URL may be invalid or inaccessible.")
            
            st.write(f"Successfully scraped {len(job_description)} characters")
            status.update(label="Step 2: Job description scraped successfully", state="complete")
            
        except Exception as e:
            status.update(label="Step 2: Scraping failed", state="error")
            raise Exception(f"Failed to scrape job posting: {str(e)}")
    
    # Step 3: Tailor resume using AI
    with st.status("Step 3: Tailoring resume with AI...", expanded=True) as status:
        st.write("Initializing Gemini API...")
        
        try:
            # Set API key in environment for ResumeTailor
            os.environ["GEMINI_API_KEY"] = api_key
            
            tailor = ResumeTailor()
            st.write("Generating optimized resume...")
            
            tailored_resume = tailor.tailor_resume(resume_text, job_description)
            
            if not tailored_resume or not tailored_resume.strip():
                raise ValueError("AI returned empty response. Please try again.")
            
            st.write("Resume optimization complete")
            status.update(label="Step 3: Resume tailored successfully", state="complete")
            
            return tailored_resume
            
        except Exception as e:
            status.update(label="Step 3: AI processing failed", state="error")
            raise Exception(f"Failed to tailor resume: {str(e)}")


def main():
    """Main Streamlit application."""
    setup_encoding()
    
    # Page configuration
    st.set_page_config(
        page_title="Resume Tailor AI",
        page_icon="📄",
        layout="wide"
    )
    
    # Title
    st.title("Resume Tailor AI")
    st.markdown("Optimize your resume for any job posting using AI-powered analysis.")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # File uploader
        st.subheader("1. Upload Resume")
        resume_file = st.file_uploader(
            "Upload your resume (PDF only)",
            type=["pdf"],
            help="Upload your current resume in PDF format"
        )
        
        # API Key input
        st.subheader("2. API Key")
        api_key_input = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Enter your API key or set GEMINI_API_KEY in .env file"
        )
        
        st.markdown("---")
        st.caption("Resume Tailor AI v1.0")
    
    # Main area
    st.header("Job Details")
    
    # Job URL input
    job_url = st.text_input(
        "Job Description URL",
        placeholder="https://example.com/job-posting",
        help="Enter the URL of the job posting you want to apply for"
    )
    
    # Tailor button
    if st.button("Tailor My Resume", type="primary", use_container_width=True):
        # Validation
        errors = []
        
        if not resume_file:
            errors.append("Please upload your resume (PDF)")
        
        if not job_url or not job_url.strip():
            errors.append("Please enter a job description URL")
        
        try:
            api_key = get_api_key(api_key_input)
        except ValueError as e:
            errors.append(str(e))
            api_key = None
        
        # Display errors if any
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Process resume tailoring
            try:
                tailored_resume = process_resume_tailoring(
                    resume_file,
                    job_url,
                    api_key
                )
                
                # Display success
                st.success("Resume tailoring completed successfully!")
                
                # Results section
                st.header("Results")
                
                # Display with Markdown rendering for beautiful formatting
                st.markdown(tailored_resume)
                
                # Download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download button with Markdown format
                    st.download_button(
                        label="Download as Markdown",
                        data=tailored_resume,
                        file_name="tailored_resume.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col2:
                    # Download button with PDF format
                    try:
                        pdf_bytes = save_as_pdf(tailored_resume)
                        st.download_button(
                            label="Download as PDF",
                            data=pdf_bytes,
                            file_name="tailored_resume.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as pdf_error:
                        st.error(f"PDF generation failed: {str(pdf_error)}")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your inputs and try again.")


if __name__ == "__main__":
    main()
