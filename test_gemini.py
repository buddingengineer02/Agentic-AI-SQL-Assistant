import os
from dotenv import load_dotenv
from crewai import LLM

# Load .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("No GOOGLE_API_KEY found in environment or .env file.")
    exit(1)
    
os.environ["GEMINI_API_KEY"] = api_key

# Test multiple common model identifiers for Gemini on CrewAI/LiteLLM
models = [
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-flash-latest",
    "gemini/gemini-1.5-flash-8b",
    "gemini/gemini-1.5-pro",
    "gemini/gemini-2.0-flash",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-1.5-flash-001"
]

print(f"Using API Key: {api_key[:10]}...")

for m in models:
    try:
        print(f"\n--- Testing model: {m} ---")
        llm = LLM(model=m, api_key=api_key, temperature=0.1)
        response = llm.call([{"role": "user", "content": "Say hello"}])
        print(f"SUCCESS: {response}")
        print(f"Model {m} is working!")
        break
    except Exception as e:
        print(f"FAILED: {e}")
