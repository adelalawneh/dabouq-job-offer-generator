import google.generativeai as genai
from PIL import Image

from services.helpers import extract_json


def extract_document_data(uploaded_file, api_key):
    genai.configure(api_key=api_key)
    image = Image.open(uploaded_file)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = """
    Analyze this Passport / ID / IQAMA.

    Extract:
    - full_name
    - nationality
    - document_number

    Return STRICT JSON ONLY.

    {
      "full_name": "",
      "nationality": "",
      "document_number": ""
    }
    """

    response = model.generate_content([prompt, image])
    return extract_json(response.text)
