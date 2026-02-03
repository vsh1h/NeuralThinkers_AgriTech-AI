from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Listing available models using google-genai SDK:")
try:
    for m in client.models.list():
        print(f"Name: {m.name}, Display Name: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")
