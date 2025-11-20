import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY in .env")
    exit()

genai.configure(api_key=api_key)

print("Available models that support generateContent:")
for m in genai.list_models():
    if "generateContent" in getattr(m, "supported_generation_methods", []):
        print("-", m.name)
