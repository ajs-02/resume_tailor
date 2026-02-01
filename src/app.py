import os
import sys
import asyncio
import tempfile
import json
import streamlit as st
from dotenv import load_dotenv

# Import local modules
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
    if user_provided_key and user_provided_key.strip():
        return user_provided_key.strip()
    load_dotenv()
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key
    raise ValueError("No API key provided. Please enter your Gemini API key.")

async def scrape_job_async(url: str) -> str:
    async with JobScraper() as scraper:
        return await scraper.scrape_job(url)

def process_resume_tailoring(resume_file, job_url: str, api_key: str):
    # Step 1: Extract
    with st.status("Step 1: Scanning resume...", expanded=True) as status:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(resume_file.read())
            tmp_path = tmp_file.name
        try:
            resume_text = extract_text_from_pdf(tmp_path)
            status.update(label="Step 1: Resume scanned successfully", state="complete")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Step 2: Scrape
    with st.status("Step 2: Scraping job description...", expanded=True) as status:
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            job_description = asyncio.run(scrape_job_async(job_url))
            status.update(label="Step 2: Job description scraped successfully", state="complete")
        except Exception as e:
            status.update(label="Step 2: Scraping failed", state="error")
            raise Exception(f"Failed to scrape job: {str(e)}")

    # Step 3: Tailor
    with st.status("Step 3: Tailoring resume with AI...", expanded=True) as status:
        try:
            os.environ["GEMINI_API_KEY"] = api_key
            tailor = ResumeTailor()
            result = tailor.tailor_resume(resume_text, job_description)
            status.update(label="Step 3: Resume tailored successfully", state="complete")
            return result
        except Exception as e:
            status.update(label="Step 3: AI processing failed", state="error")
            raise Exception(f"Failed to tailor resume: {str(e)}")

def render_resume_editor(data):
    """
    Renders a tabbed interface to edit resume data.
    Returns the updated data dictionary.
    """
    st.subheader("📝 Edit Resume Content")
    
    # Create Tabs
    tabs = st.tabs(["👤 Contact Info", "🛠 Skills", "💼 Experience", "🚀 Projects", "🎓 Education"])
    
    # --- Tab 1: Personal Info ---
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            data['personal_info']['name'] = st.text_input("Full Name", data['personal_info'].get('name', ''), key="pi_name")
            data['personal_info']['email'] = st.text_input("Email", data['personal_info'].get('email', ''), key="pi_email")
            data['personal_info']['phone'] = st.text_input("Phone", data['personal_info'].get('phone', ''), key="pi_phone")
        with col2:
            data['personal_info']['location'] = st.text_input("Location", data['personal_info'].get('location', ''), key="pi_loc")
            data['personal_info']['linkedin'] = st.text_input("LinkedIn URL", data['personal_info'].get('linkedin', ''), key="pi_link")
            data['personal_info']['github'] = st.text_input("GitHub URL", data['personal_info'].get('github', ''), key="pi_git")

    # --- Tab 2: Skills ---
    with tabs[1]:
        st.info("Edit skills as a comma-separated list.")
        skills_str = ", ".join(data.get('skills', []))
        # Unique key 'skills_editor' prevents conflicts
        new_skills = st.text_area("Skills List", value=skills_str, height=150, key="skills_editor")
        # Convert back to list
        data['skills'] = [s.strip() for s in new_skills.split(',') if s.strip()]

    # --- Tab 3: Experience ---
    with tabs[2]:
        st.info("Edit your work history. Bullets should be separated by new lines.")
        if 'experience' not in data:
            data['experience'] = []
            
        for i, job in enumerate(data['experience']):
            with st.expander(f"{job.get('role', 'Job')} at {job.get('company', 'Company')}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                # We use 'key' to store the index, keeping the label clean
                job['role'] = c1.text_input("Role", job.get('role', ''), key=f"exp_role_{i}")
                job['company'] = c2.text_input("Company", job.get('company', ''), key=f"exp_comp_{i}")
                
                c3, c4 = st.columns(2)
                job['duration'] = c3.text_input("Dates", job.get('duration', ''), key=f"exp_date_{i}")
                job['location'] = c4.text_input("Location", job.get('location', ''), key=f"exp_loc_{i}")
                
                bullets_str = "\n".join(job.get('points', []))
                new_bullets = st.text_area("Bullets (One per line)", value=bullets_str, height=200, key=f"exp_bullets_{i}")
                job['points'] = [b.strip() for b in new_bullets.split('\n') if b.strip()]

    # --- Tab 4: Projects ---
    with tabs[3]:
        if 'projects' not in data:
            data['projects'] = []
            
        for i, proj in enumerate(data['projects']):
            with st.expander(f"{proj.get('title', 'Project')}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                proj['title'] = c1.text_input("Project Title", proj.get('title', ''), key=f"proj_title_{i}")
                proj['role'] = c2.text_input("Role", proj.get('role', ''), key=f"proj_role_{i}")
                
                proj['duration'] = st.text_input("Dates", proj.get('duration', ''), key=f"proj_date_{i}")
                
                bullets_str = "\n".join(proj.get('points', []))
                new_bullets = st.text_area("Project Details (One per line)", value=bullets_str, height=150, key=f"proj_desc_{i}")
                proj['points'] = [b.strip() for b in new_bullets.split('\n') if b.strip()]

    # --- Tab 5: Education ---
    with tabs[4]:
        if 'education' not in data:
            data['education'] = []
            
        for i, edu in enumerate(data['education']):
            with st.expander(f"{edu.get('school', 'School')}"):
                c1, c2 = st.columns(2)
                edu['school'] = c1.text_input("School", edu.get('school', ''), key=f"edu_school_{i}")
                edu['degree'] = c2.text_input("Degree", edu.get('degree', ''), key=f"edu_degree_{i}")
                edu['duration'] = st.text_input("Graduation Date", edu.get('duration', ''), key=f"edu_date_{i}")

    return data

def main():
    setup_encoding()
    st.set_page_config(page_title="Resume Tailor AI", page_icon="📄", layout="wide")
    
    if 'resume_data' not in st.session_state:
        st.session_state['resume_data'] = None

    st.title("Resume Tailor AI")

    with st.sidebar:
        st.header("Configuration")
        resume_file = st.file_uploader("1. Upload Resume (PDF)", type=["pdf"])
        api_key_input = st.text_input("2. Gemini API Key", type="password")
        
    job_url = st.text_input("Job Description URL", placeholder="https://example.com/job")

    if st.button("Tailor My Resume", type="primary"):
        if not resume_file or not job_url:
            st.error("Please upload a resume and provide a URL.")
        else:
            try:
                api_key = get_api_key(api_key_input)
                result = process_resume_tailoring(resume_file, job_url, api_key)
                st.session_state['resume_data'] = result
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # --- Display Logic ---
    if st.session_state['resume_data'] is not None:
        st.divider()
        
        # 1. Executive Summary
        summary = st.session_state['resume_data'].get("executive_summary", [])
        with st.expander("📊 Executive Summary of Changes", expanded=True):
            if isinstance(summary, list):
                for item in summary:
                    st.markdown(f"- {item}")
            else:
                st.markdown(summary)
        
        # 2. The Editor (Updates Session State directly)
        st.session_state['resume_data'] = render_resume_editor(st.session_state['resume_data'])
        
        # 3. Actions
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            try:
                # Generate PDF from the EDITED data
                pdf_bytes = save_as_pdf(st.session_state['resume_data'])
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF Error: {str(e)}")
        
        with c2:
            json_data = json.dumps(st.session_state['resume_data'], indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name="resume_data.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()