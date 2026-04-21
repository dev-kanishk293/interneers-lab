import json
import os
import django
from google import genai
from dotenv import load_dotenv
from pydantic import ValidationError
from mongoengine import connect

# Load .env
load_dotenv()

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django.conf import settings
from products.models import ProductDocument
from products.validators import ProductListValidator

# Initializing Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize MongoDB connection
connect(alias="default", **settings.MONGODB_SETTINGS)

def generate_products_gemini(count=50):
    prompt = f"""
    Generate {count} products for a toy store. 
    Each product should have:
    - name: String (concise)
    - description: String (max 500 chars)
    - category: String (e.g., 'Action Figures', 'Board Games')
    - price: Float (between 5.0 and 200.0)
    - brand: String (optional)
    - quantity: Integer (between 1 and 100)
    - category_ids: List of integers (empty for now)
    
    Return the result as a strictly valid JSON object with a single key 'products' which is a list of these objects.
    """
    
    print(f"Requesting {count} products from Gemini 2.0 Flash...")
    
    try:
        # Requesting JSON output through the new config
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        
        raw_json = response.text
        data = json.loads(raw_json)
        
        # Task 3: Pydantic Validation
        validated_data = ProductListValidator(**data)
        
        saved_count = 0
        for product_data in validated_data.products:
            doc_data = product_data.model_dump()
            product_doc = ProductDocument(**doc_data)
            product_doc.save()
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"Saved {saved_count} products...")
                
        print(f"Successfully validated and saved {saved_count} products to MongoDB (via New Gemini Client).")
        
    except ValidationError as e:
        print(f"Validation Error: {e.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found in .env. Please add it first.")
    else:
        generate_products_gemini(50)
