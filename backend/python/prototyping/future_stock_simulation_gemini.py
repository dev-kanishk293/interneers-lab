import json
import os
from google import genai
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Client setup
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Task 4: Generate 10 Future Stock Events
def generate_future_stock_events_gemini():
    prompt = """
    Generate 10 "Future Stock Events" for a retail dashboard.
    Examples:
    - "Expected delivery of 50 Toy Cars on Feb 1st from supplier XYZ"
    - "Seasonal demand spike for Board Games predicted for late March"
    - "Bulk return of 20 Action Figures expected on Feb 15th"
    
    Return the result as a strictly valid JSON object with a single key 'events' which is a list of strings.
    """
    
    print("Requesting future stock events from Gemini 2.5 Flash...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        
        raw_json = response.text
        data = json.loads(raw_json)
        
        events = data.get("events", [])
        
        print(f"\n--- Generated {len(events)} Future Stock Events (via Gemini 2.5) ---")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event}")
            print(f"   [Audit Log]: Simulated log for: {event[:30]}...")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found in .env. Please add it first.")
    else:
        generate_future_stock_events_gemini()
