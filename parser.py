import os
import json
import base64
import gc  # Garbage Collector to force memory cleanup
from io import BytesIO
from openai import OpenAI
from pdf2image import convert_from_path
from database import save_teacher_to_mongo

# Initialize AI client with your OpenRouter Key
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "your_key_here")
)

def encode_image(image):
    """Converts a PIL image to a base64 string for the AI vision model."""
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=85) # Reduced quality to save RAM
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def run_ai_parser(pdf_path):
    """Processes PDF pages one-by-one to stay under Render's 512MB RAM limit."""
    
    # Path for Windows; Render uses system-installed poppler automatically
    poppler = r'C:\poppler-25.12.0\Library\bin' if not os.environ.get('RENDER') else None
    
    print(f"Starting memory-optimized parsing for: {pdf_path}")

    try:
        # Optimization: Lower DPI (100) and thread_count (1) to prevent RAM spikes
        pages = convert_from_path(
            pdf_path, 
            poppler_path=poppler,
            dpi=100, 
            fmt="jpeg", 
            thread_count=1 
        )

        for i, page_img in enumerate(pages):
            print(f"Processing Page {i+1} of {len(pages)}...")
            
            base64_image = encode_image(page_img)
            
            # Send to Gemini 2.0 Flash via OpenRouter
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

            # Parse and save to MongoDB Atlas
            content = response.choices[0].message.content.strip()
            # Clean AI response to ensure it's valid JSON
            clean_json = content.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            save_teacher_to_mongo(data)

            # CRITICAL: Force memory cleanup after each page
            del page_img
            gc.collect()

        print("Successfully updated MongoDB with all pages.")

    except Exception as e:
        print(f"Parser Error: {str(e)}")