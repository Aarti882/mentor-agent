import os
import re
from pypdf import PdfReader
from io import BytesIO
from google import genai
from google.genai import types

def extract_text_from_pdf(pdf_bytes):
    """Extracts all text content from PDF file bytes."""
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def clean_text(text):
    """Basic text cleaning: normalization of spaces and removals."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_gemini_client(api_key=None):
    """Initializes the new Google GenAI client.
    
    Checks in this order:
    1. Passed API key
    2. GEMINI_API_KEY environment variable
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as e:
        print(f"Failed to initialize GenAI client: {e}")
        return None

def call_gemini(prompt, api_key=None, system_instruction=None, response_schema=None):
    """Convenience function to generate content from Gemini-2.5-flash."""
    client = get_gemini_client(api_key)
    if not client:
        raise ValueError("Gemini API key is missing. Please set GEMINI_API_KEY in the environment or Streamlit sidebar.")
    
    config = types.GenerateContentConfig(
        temperature=0.2,
        system_instruction=system_instruction
    )
    
    if response_schema:
        config.response_mime_type = "application/json"
        config.response_schema = response_schema
        
    try:
        # Using the standard gemini-2.5-flash model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {e}")
