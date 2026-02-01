import asyncio
import json
import os
import sys
import tempfile

import streamlit as st
from dotenv import load_dotenv

from config import API_KEY_NAMES, FREE_TIER_MAX_REQUESTS, STREAMLIT_CONFIG, STYLE_CSS
from exporter import save_as_pdf
from ingest import extract_text_from_pdf
from scraper import JobScraper
from tailor import ResumeTailor

def setup_encoding():
    """Configure UTF-8 encoding for Windows console output."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')


def load_css():
    """Load custom CSS styles from file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, STYLE_CSS)
    try:
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def get_api_key(user_provided_key: str, provider: str) -> str:
    """Resolve API key from user input or environment variables.

    Args:
        user_provided_key: API key entered by user
        provider: AI provider name (google/openai/anthropic)

    Returns:
        Valid API key string

    Raises:
        ValueError: If no API key is found
    """
    if user_provided_key and user_provided_key.strip():
        return user_provided_key.strip()

    load_dotenv()
    env_key_name = API_KEY_NAMES.get(provider, f"{provider.upper()}_API_KEY")
    env_key = os.getenv(env_key_name)

    if env_key:
        return env_key

    raise ValueError(f"No API key provided. Please enter your {provider.capitalize()} API Key.")

async def scrape_job_async(url: str) -> str:
    """Async wrapper for job scraping."""
    async with JobScraper() as scraper:
        return await scraper.scrape_job(url)


def process_resume_tailoring(resume_file, job_url: str, api_key: str, provider: str = "google"):
    """Process resume tailoring workflow: extract, scrape, tailor.

    Args:
        resume_file: Uploaded PDF file object
        job_url: Job posting URL
        api_key: API key for LLM provider
        provider: AI provider name (default: google)

    Returns:
        Structured resume data dictionary
    """
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

    with st.status("Step 2: Scraping job description...", expanded=True) as status:
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            job_description = asyncio.run(scrape_job_async(job_url))
            status.update(label="Step 2: Job description scraped successfully", state="complete")
        except Exception as e:
            status.update(label="Step 2: Scraping failed", state="error")
            raise Exception(f"Failed to scrape job: {str(e)}")

    with st.status("Step 3: Tailoring resume...", expanded=True) as status:
        try:
            os.environ[API_KEY_NAMES["google"]] = api_key
            tailor = ResumeTailor(provider=provider, api_key=api_key)
            result = tailor.tailor_resume(resume_text, job_description)
            status.update(label="Step 3: Tailoring complete", state="complete")
            return result
        except Exception as e:
            status.update(label="Step 3: Processing failed", state="error")
            raise Exception(f"Failed to tailor resume: {str(e)}")


def render_resume_editor(data):
    """Render tabbed interface for editing resume sections."""
    st.subheader("Edit Content")
    tabs = st.tabs(["Contact Info", "Skills", "Experience", "Projects", "Education"])

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

    with tabs[1]:
        st.info("Edit skills as a comma-separated list.")
        skills_str = ", ".join(data.get('skills', []))
        new_skills = st.text_area("Skills List", value=skills_str, height=150, key="skills_editor")
        data['skills'] = [s.strip() for s in new_skills.split(',') if s.strip()]

    with tabs[2]:
        st.info("Edit your work history. Bullets should be separated by new lines.")
        if 'experience' not in data:
            data['experience'] = []

        for i, job in enumerate(data['experience']):
            with st.expander(f"{job.get('role', 'Job')} at {job.get('company', 'Company')}", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                job['role'] = c1.text_input("Role", job.get('role', ''), key=f"exp_role_{i}")
                job['company'] = c2.text_input("Company", job.get('company', ''), key=f"exp_comp_{i}")

                c3, c4 = st.columns(2)
                job['duration'] = c3.text_input("Dates", job.get('duration', ''), key=f"exp_date_{i}")
                job['location'] = c4.text_input("Location", job.get('location', ''), key=f"exp_loc_{i}")

                bullets_str = "\n".join(job.get('points', []))
                new_bullets = st.text_area("Bullets (One per line)", value=bullets_str, height=200, key=f"exp_bullets_{i}")
                job['points'] = [b.strip() for b in new_bullets.split('\n') if b.strip()]

    with tabs[3]:
        if 'projects' not in data:
            data['projects'] = []

        for i, proj in enumerate(data['projects']):
            with st.expander(f"{proj.get('title', 'Project')}", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                proj['title'] = c1.text_input("Project Title", proj.get('title', ''), key=f"proj_title_{i}")
                proj['role'] = c2.text_input("Role", proj.get('role', ''), key=f"proj_role_{i}")
                proj['duration'] = st.text_input("Dates", proj.get('duration', ''), key=f"proj_date_{i}")

                bullets_str = "\n".join(proj.get('points', []))
                new_bullets = st.text_area("Project Details (One per line)", value=bullets_str, height=150, key=f"proj_desc_{i}")
                proj['points'] = [b.strip() for b in new_bullets.split('\n') if b.strip()]

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
    """Main application entry point."""
    setup_encoding()
    st.set_page_config(**STREAMLIT_CONFIG)
    load_css()

    if 'resume_data' not in st.session_state:
        st.session_state['resume_data'] = None

    if 'usage_count' not in st.session_state:
        st.session_state['usage_count'] = 0

    st.title("Resume Tailor")
    st.markdown("""
    <p style='font-size: 1.1rem; color: #9CA3AF; margin-bottom: 2rem;'>
        Optimize your resume for any job posting. Analyze requirements and align your experience.
    </p>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Configuration")

        provider = st.radio(
            "Select AI Model",
            options=["google", "openai", "anthropic"],
            format_func=lambda x: x.capitalize(),
            horizontal=True,
            help="Choose which AI provider to use."
        )

        limit_msg = f"Leave blank to use free tier ({FREE_TIER_MAX_REQUESTS - st.session_state['usage_count']} tries left)"
        api_label = f"{provider.capitalize()} API Key"
        api_key_input = st.text_input(api_label, type="password", help=limit_msg)

        resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

        st.markdown("---")
        st.header("About")
        st.markdown("""
        **Resume Tailor v1.4**

        Built by **Amanjeet Singh**.
        """)

        c1, c2 = st.columns(2)
        with c1:
            st.link_button("LinkedIn", "https://linkedin.com/in/aj-singh02", use_container_width=True)
        with c2:
            st.link_button("GitHub", "https://github.com/Amanjeet-Singh", use_container_width=True)

        st.markdown("---")

    st.subheader("Target Job")
    job_url = st.text_input("Job Description URL", placeholder="https://linkedin.com/jobs/view/...")

    if st.button("Tailor Resume", type="primary", use_container_width=True):
        if not resume_file or not job_url:
            st.error("Please upload a resume and provide a URL.")
        else:
            can_proceed = True
            using_free_tier = False

            if not api_key_input:
                using_free_tier = True
                if st.session_state['usage_count'] >= FREE_TIER_MAX_REQUESTS:
                    st.error(f"Free trial limit reached ({FREE_TIER_MAX_REQUESTS}/{FREE_TIER_MAX_REQUESTS}). Please enter your own API key to continue.")
                    can_proceed = False

            if can_proceed:
                try:
                    api_key = get_api_key(api_key_input, provider)

                    if using_free_tier:
                        st.session_state['usage_count'] += 1

                    result = process_resume_tailoring(resume_file, job_url, api_key, provider)
                    st.session_state['resume_data'] = result
                    st.rerun()

                except ValueError as ve:
                    st.warning(str(ve))
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if st.session_state['resume_data'] is not None:
        st.divider()

        summary = st.session_state['resume_data'].get("executive_summary", [])
        with st.expander("Executive Summary of Changes", expanded=True):
            if isinstance(summary, list):
                for item in summary:
                    st.markdown(f"- {item}")
            else:
                st.markdown(summary)

        st.session_state['resume_data'] = render_resume_editor(st.session_state['resume_data'])

        st.divider()
        st.subheader("Download")
        c1, c2 = st.columns(2)
        with c1:
            try:
                pdf_bytes = save_as_pdf(st.session_state['resume_data'])
                st.download_button(
                    label="Download PDF",
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
                label="Download JSON",
                data=json_data,
                file_name="resume_data.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()