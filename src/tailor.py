import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import the different Brains
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class ResumeTailor:
    def __init__(self, provider="google", api_key=None):
        self.provider = provider
        self.api_key = api_key
        self.llm = self._create_llm()

    def _create_llm(self):
        """
        Factory method to initialize the selected LLM.
        We prioritize 'Flash' and 'Turbo' class models for speed.
        """
        try:
            if self.provider == "google":
                # FASTEST: Gemini 2.0 Flash
                # Confirmed available from your 'check_models.py' list
                return ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash", 
                    google_api_key=self.api_key,
                    temperature=0.2
                )
            elif self.provider == "openai":
                # FAST & SMART: GPT-4o
                # Excellent balance of speed and intelligence
                return ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.api_key,
                    temperature=0.2
                )
            elif self.provider == "anthropic":
                # BALANCED: Claude 3.5 Sonnet
                # Fast enough for UI use, smarter than Haiku
                return ChatAnthropic(
                    model="claude-3-5-sonnet-latest",
                    api_key=self.api_key,
                    temperature=0.2
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            raise ValueError(f"Failed to initialize {self.provider} model: {str(e)}")

    def tailor_resume(self, resume_text, job_description):
        """
        Tailors the resume using the selected LLM.
        """
        # Strict JSON Schema Prompt
        # NOTICE: The JSON schema below uses DOUBLE curly braces {{ }} to escape them!
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

        # Create the chain
        chain = prompt | self.llm | StrOutputParser()

        # Run the chain
        response = chain.invoke({
            "resume": resume_text,
            "job": job_description
        })

        # Parse the result
        return self._clean_and_parse_json(response)

    def _clean_and_parse_json(self, response_text):
        """
        Helper to ensure we get valid JSON even if the LLM hallucinates markdown.
        """
        try:
            # Strip markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Fallback for debugging
            return {
                "executive_summary": ["Error parsing AI response. Please try again."],
                "personal_info": {},
                "skills": [],
                "experience": [],
                "projects": [],
                "education": []
            }