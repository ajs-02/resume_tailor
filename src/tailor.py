import os
import sys
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
    
    def tailor_resume(self, resume_text: str, job_description: str) -> str:
        """
        Tailors a resume to match a specific job description.
        
        Args:
            resume_text (str): The original resume text
            job_description (str): The job posting description
            
        Returns:
            str: The tailored resume text
        """
        print("[INFO] Starting resume tailoring process...")
        
        prompt = f"""You are an expert resume optimizer. Your task is to tailor the following resume to match the job description provided.

INSTRUCTIONS:
1. Analyze the job description to identify key skills, requirements, and keywords
2. Optimize the resume to highlight relevant experience and skills that match the job
3. Maintain the original resume structure and format
4. Keep all information truthful - do not fabricate experience
5. Emphasize achievements and metrics that align with the job requirements
6. Use industry-standard keywords from the job description where appropriate

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_text}

Please provide the optimized resume:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            print("[INFO] Resume tailoring completed successfully")
            return response.text
            
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
