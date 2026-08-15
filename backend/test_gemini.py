import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load your .env file
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("--- Models Available for Your API Key ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Failed to authenticate: {e}")