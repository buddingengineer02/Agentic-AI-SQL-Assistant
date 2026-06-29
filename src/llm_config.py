import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

def get_llm():
    """
    Instantiates and returns the official CrewAI LLM instance for Gemini 2.5 Flash.
    Using gemini/gemini-2.5-flash avoids 404 errors on v1beta endpoints.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY in the .env file.")
    
    # LiteLLM (used by CrewAI) standardizes on GEMINI_API_KEY for the gemini/ prefix.
    os.environ["GEMINI_API_KEY"] = api_key
    
    return LLM(
        model="gemini/gemini-2.5-flash",
        api_key=api_key,
        temperature=0.1,
        max_tokens=1000
    )
