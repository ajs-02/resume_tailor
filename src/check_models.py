import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file.")
    print("Please make sure you have a .env file with your key.")
else:
    try:
        genai.configure(api_key=api_key)
        print(f"API Key found. querying Google servers for available models...\n")
        
        print("--- AVAILABLE MODELS ---")
        found = False
        for m in genai.list_models():
            # We only care about models that can generate text (generateContent)
            if 'generateContent' in m.supported_generation_methods:
                print(f"NAME: {m.name}")
                found = True
        
        if not found:
            print("No text generation models found. Check your API key permissions.")
            
    except Exception as e:
        print(f"Error querying API: {e}")