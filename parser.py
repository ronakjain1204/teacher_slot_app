import os
import json
import base64
import gc 
from io import BytesIO
from openai import OpenAI
from pdf2image import convert_from_path
from database import save_teacher_to_mongo

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "your_key_here")
)

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=85) 
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def run_ai_parser(pdf_path):
    poppler = r'C:\poppler-25.12.0\Library\bin' if not os.environ.get('RENDER') else None
    print(f"Starting detailed parsing (Free & Busy slots) for: {pdf_path}")

    try:
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
            
            # IMPROVED PROMPT: Instructs AI to map the whole schedule
            prompt = (
                "Analyze this timetable page. Extract the teacher's name. "
                "For every time slot (9:30, 10:20, 11:20, 12:10, 1:05, 1:55, 2:45, 3:35) across all days (MON-SAT), "
                "determine if the teacher is 'BUSY' or 'FREE'. "
                "Return JSON: {'name': 'Name', 'schedule': [{'day': 'MONDAY', 'time': '09:30', 'status': 'FREE'}, "
                "{'day': 'MONDAY', 'time': '10:20', 'status': 'BUSY'}]}. Return ONLY JSON."
            )

            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )

            content = response.choices[0].message.content.strip()
            clean_json = content.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            # Save to MongoDB
            save_teacher_to_mongo(data)

            del page_img
            gc.collect()

        print("Successfully updated MongoDB with full schedules.")

    except Exception as e:
        print(f"Parser Error: {str(e)}")