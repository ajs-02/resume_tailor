import os

import google.generativeai as genai
from dotenv import load_dotenv

from config import API_KEY_NAMES

load_dotenv()
api_key = os.getenv(API_KEY_NAMES["google"])

if not api_key:
    print(f"[ERROR] {API_KEY_NAMES['google']} not found in .env file.")
    print("[INFO] Please make sure you have a .env file with your key.")
else:
    try:
        genai.configure(api_key=api_key)
        print("[INFO] API Key found. Querying Google servers for available models...\n")

        print("--- AVAILABLE MODELS ---")
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"NAME: {m.name}")
                found = True

        if not found:
            print("[WARNING] No text generation models found. Check your API key permissions.")

    except Exception as e:
        print(f"[ERROR] Error querying API: {e}")