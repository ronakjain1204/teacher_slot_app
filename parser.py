import os
import json
import base64
import time
from io import BytesIO
from openai import OpenAI
from pdf2image import convert_from_path
from teacher_slot_app.database import save_teacher_to_mongo

# Configure kar rahe api key aur poppler path
MY_API_KEY = "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"
POPPLER_PATH = r'C:\poppler-25.12.0\Library\bin' 
PDF_FILE_PATH = "data/B3 3rd year teacherwise_5th Jan.pdf"

# Correct api fetch karke client initialize
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=MY_API_KEY,
)

# Image ko base64 me encode karne ka function
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Yeh Function AI parser ko run karega
def run_ai_parser(pdf_path):
    print("Converting PDF to images...")
    # Poppler path specify karte hue PDF ko images me convert karna
    pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    
    for i, page_img in enumerate(pages):
        print(f"Processing Teacher {i+1} of {len(pages)}...")
        base64_image = encode_image(page_img)
        
        try:
            # AI model ko call karna with image input
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-001", # Ye wala isliye kiya kyuki image input support karta hai
                messages=[ #yaha hum prompt bhej rahe hain
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract teacher name and busy slots into JSON format: {'name': 'Teacher Name', 'busy_slots': [{'day': 'MONDAY', 'time': '09:30', 'activity': '...'}]}. Return ONLY JSON."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            
            # Response ko json se parse karke mongo me save kar rahe
            content = response.choices[0].message.content.strip()
            clean_json = content.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            
            save_teacher_to_mongo(data)
            print(f"Successfully saved: {data.get('name')}")
            
            # timer isliye lagaya hai taki rate limit na ho
            time.sleep(5) 

        except Exception as e:
            print(f"Error on page {i+1}: {e}")
            if "401" in str(e):
                print("Authentication failed. Please check your OpenRouter credits and API key.")
                break

if __name__ == "__main__":
    run_ai_parser(PDF_FILE_PATH)