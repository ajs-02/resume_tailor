import os
import sys
import json
import re
from dotenv import load_dotenv
from google import genai


class ResumeTailor:
    """
    Resume tailoring service using Google Gemini API.
    """
    
    def __init__(self):
        """
        Initialize the ResumeTailor with Gemini API client.
        """
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
        print(f"[INFO] ResumeTailor initialized with model: {self.model_name}")
    
    def tailor_resume(self, resume_text: str, job_description: str) -> dict:
        """
        Tailors a resume to match a specific job description.
        
        Args:
            resume_text (str): The original resume text
            job_description (str): The job posting description
            
        Returns:
            dict: Structured dictionary with resume sections
        """
        print("[INFO] Starting resume tailoring process...")
        
        prompt = f"""You are an expert resume optimizer. Your task is to extract, structure, and optimize the following resume to match the job description provided.

INSTRUCTIONS:
1. Analyze the job description to identify key skills, requirements, and keywords
2. Optimize the resume to highlight relevant experience and skills that match the job
3. Keep all information truthful - do not fabricate experience
4. Emphasize achievements and metrics that align with the job requirements
5. Use industry-standard keywords from the job description where appropriate

CRITICAL DATA CLEANING RULES:
- Do NOT include icons, emojis, or special characters (like map markers, phone icons, envelope icons)
- Clean location and phone fields to contain ONLY text and standard punctuation
- Use standard ASCII characters only
- Remove any Unicode symbols from the original resume

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_text}

RESPONSE FORMAT:
You MUST respond with ONLY valid JSON in this EXACT structure (no markdown code fencing):

{{
  "executive_summary": ["Change/optimization 1", "Change/optimization 2", "Change/optimization 3"],
  "personal_info": {{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1 (555) 123-4567",
    "linkedin": "https://linkedin.com/in/username",
    "github": "https://github.com/username",
    "location": "City, State"
  }},
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Jan 2020 - Present",
      "location": "City, State",
      "points": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "role": "Your Role",
      "duration": "Jan 2020 - Mar 2020",
      "points": ["Description 1", "Description 2"]
    }}
  ],
  "education": [
    {{
      "school": "University Name",
      "degree": "Bachelor of Science in Computer Science",
      "duration": "Sep 2016 - Jun 2020",
      "location": "City, State"
    }}
  ]
}}

CRITICAL RULES:
- Return ONLY the JSON object
- Do not wrap it in code fences
- Ensure all fields are clean ASCII text
- If a field is missing from the original resume, use an empty string "" or empty array []
- Optimize bullet points to match job requirements"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            raw_text = response.text.strip()
            print("[INFO] Resume tailoring completed, parsing response...")
            
            # Strip markdown code fencing if present
            cleaned_text = re.sub(r'^```json\s*', '', raw_text)
            cleaned_text = re.sub(r'^```\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            try:
                result = json.loads(cleaned_text)
                
                # Validate required top-level keys
                required_keys = ["executive_summary", "personal_info", "skills", "experience", "education"]
                missing_keys = [key for key in required_keys if key not in result]
                
                if missing_keys:
                    print(f"[WARNING] Missing keys in response: {missing_keys}")
                
                print("[INFO] Successfully parsed structured JSON response")
                return result
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                print(f"[ERROR] JSON parsing failed: {parse_error}")
                print(f"[DEBUG] Raw response: {raw_text[:500]}")
                print("[INFO] Returning fallback response")
                
                # Fallback: return minimal structure with error
                return {
                    "executive_summary": ["Parsing Error: Unable to parse AI response into structured format"],
                    "personal_info": {
                        "name": "Error",
                        "email": "",
                        "phone": "",
                        "linkedin": "",
                        "github": "",
                        "location": ""
                    },
                    "skills": [],
                    "experience": [],
                    "projects": [],
                    "education": [],
                    "raw_error": raw_text[:1000]
                }
            
        except Exception as e:
            error_msg = f"Error during resume tailoring: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)
    
    def test_connection(self, test_message: str = "Hello, are you ready?") -> str:
        """
        Tests the connection to Gemini API.
        
        Args:
            test_message (str): Test message to send
            
        Returns:
            str: Response from the API
        """
        print(f"[INFO] Testing connection with message: '{test_message}'")
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=test_message
            )
            
            print("[INFO] Connection test successful")
            return response.text
            
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)


def main():
    """
    Test the ResumeTailor with a simple connection test.
    """
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    print("-" * 60)
    print("[INFO] Starting ResumeTailor connection test...")
    print("-" * 60)
    
    try:
        tailor = ResumeTailor()
        
        print(f"[INFO] Using model version: {tailor.model_name}")
        
        test_response = tailor.test_connection("Hello, are you ready?")
        
        print("\n" + "-" * 60)
        print("[INFO] API Response:")
        print("-" * 60)
        print(test_response)
        print("-" * 60)
        
        print("\n[INFO] Connection test completed successfully")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        
        # Attempt to list available models for debugging
        print("\n[INFO] Attempting to list available models for debugging...")
        try:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
                print("[INFO] Available models:")
                print("-" * 60)
                
                models = client.models.list()
                for model in models:
                    print(f"  - {model.name}")
                
                print("-" * 60)
            else:
                print("[ERROR] Cannot list models: GEMINI_API_KEY not found")
        except Exception as list_error:
            print(f"[ERROR] Failed to list models: {list_error}")
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
