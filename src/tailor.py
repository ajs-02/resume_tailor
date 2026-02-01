import json
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from config import LLM_TEMPERATURE, MODELS


class ResumeTailor:
    """Resume tailoring service with multi-provider LLM support."""

    def __init__(self, provider="google", api_key=None):
        """Initialize ResumeTailor with specified AI provider.

        Args:
            provider: AI provider name (google/openai/anthropic)
            api_key: API key for the provider
        """
        self.provider = provider
        self.api_key = api_key
        self.llm = self._create_llm()

    def _create_llm(self):
        """Factory method to initialize LLM based on provider."""
        try:
            if self.provider == "google":
                return ChatGoogleGenerativeAI(
                    model=MODELS["google"],
                    google_api_key=self.api_key,
                    temperature=LLM_TEMPERATURE
                )
            elif self.provider == "openai":
                return ChatOpenAI(
                    model=MODELS["openai"],
                    api_key=self.api_key,
                    temperature=LLM_TEMPERATURE
                )
            elif self.provider == "anthropic":
                return ChatAnthropic(
                    model=MODELS["anthropic"],
                    api_key=self.api_key,
                    temperature=LLM_TEMPERATURE
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            raise ValueError(f"Failed to initialize {self.provider} model: {str(e)}")

    def tailor_resume(self, resume_text, job_description):
        """Tailor resume to match job description using LLM.

        Args:
            resume_text: Original resume content
            job_description: Target job posting content

        Returns:
            Structured resume data dictionary
        """
        system_prompt = """
        You are an expert Resume Strategist and ATS Optimizer.

        Your task is to rewrite the "Experience", "Projects", and "Skills" sections of the candidate's resume to align perfectly with the Job Description.

        **CRITICAL OUTPUT RULES:**
        1. You must output ONLY valid JSON.
        2. Do not wrap the JSON in markdown code blocks (like ```json ... ```). Just return the raw JSON string.
        3. Do not include any text before or after the JSON.

        **CONTENT INSTRUCTIONS:**
        - **"executive_summary"**: Do NOT summarize the candidate's profile. Instead, list 3-5 specific changes you made to the resume to tailor it (e.g., "Added keywords 'Python' and 'SQL' to Skills", "Rewrote 'Project Alpha' bullet points to emphasize Leadership", "Quantified achievements in 'Software Engineer' role").

        Follow this exact schema:
        {{
            "executive_summary": ["Change 1", "Change 2", "Change 3"],
            "personal_info": {{
                "name": "string",
                "email": "string",
                "phone": "string",
                "linkedin": "string (url)",
                "github": "string (url)",
                "location": "string"
            }},
            "skills": ["skill 1", "skill 2"],
            "experience": [
                {{
                    "company": "string",
                    "role": "string",
                    "duration": "string",
                    "location": "string",
                    "points": ["bullet 1", "bullet 2"]
                }}
            ],
            "projects": [
                {{
                    "title": "string",
                    "role": "string",
                    "duration": "string",
                    "points": ["bullet 1", "bullet 2"]
                }}
            ],
            "education": [
                {{
                    "school": "string",
                    "degree": "string",
                    "duration": "string",
                    "location": "string"
                }}
            ]
        }}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{job}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "resume": resume_text,
            "job": job_description
        })

        return self._clean_and_parse_json(response)

    def _clean_and_parse_json(self, response_text):
        """Clean and parse JSON response from LLM."""
        try:
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {
                "executive_summary": ["Error parsing AI response. Please try again."],
                "personal_info": {},
                "skills": [],
                "experience": [],
                "projects": [],
                "education": []
            }