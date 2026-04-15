import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def test_generation(prompt, temp):
    print(f"\n--- Testing with temperature: {temp} ---")
    
    # Gemini 2.0 Flash is recommended for new projects
    # Config includes temperature and other generation parameters
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"temperature": temp}
    )
    
    # Token count is available with a dedicated call
    token_count = client.models.count_tokens(
        model="gemini-2.0-flash",
        contents=prompt
    )
    print(f"Prompt token count: {token_count.total_tokens}")
    
    print(f"Response:\n{response.text}")
    print(f"\nUsage Stats (Estimated for Gemini Flash Free Tier):")
    print(f"Cost: $0.00 (Free Tier)")
    
    return response.text

if __name__ == "__main__":
    prompt_text = "Generate 5 product names for a toy store"
    
    # Task 1b: Experiment with temperature
    temperatures = [0.0, 0.7, 1.5]
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found in .env. Please add it first.")
    else:
        for t in temperatures:
            try:
                test_generation(prompt_text, t)
            except Exception as e:
                print(f"Error at temp {t}: {e}")
