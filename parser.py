import os
import json
import base64
from io import BytesIO
from openai import OpenAI
from pdf2image import convert_from_path
from database import save_teacher_to_mongo

# Fetch API Key from Environment Variables for safety
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "your_api_key_here")
)

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def run_ai_parser(pdf_path):
    """Processes the PDF and updates the Data Layer."""
    # Cloud check: Render doesn't need a poppler_path
    poppler = r'C:\poppler-25.12.0\Library\bin' if not os.environ.get('RENDER') else None
    pages = convert_from_path(pdf_path, poppler_path=poppler)
    
    for i, page_img in enumerate(pages):
        base64_image = encode_image(page_img)
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract teacher name and busy slots into JSON format: {'name': 'Name', 'busy_slots': [{'day': 'MONDAY', 'time': '09:30'}]}. Return ONLY JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content.replace('```json', '').replace('```', ''))
        save_teacher_to_mongo(data)