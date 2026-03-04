import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load the NEBIUS_API_KEY from your .env file
load_dotenv()

# 2. Initialize the Nebius client
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY")
)

print("--- Checking Nebius Connection ---")

try:
    # 3. Request a tiny response to verify the key
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[
            {"role": "user", "content": "Confirm connection: respond with 'System Ready'"}
        ],
        max_tokens=10
    )
    
    # 4. Success message
    print(f"Response from Nebius: {completion.choices[0].message.content}")
    print("✅ API Key is valid and working!")

except Exception as e:
    # 5. Friendly error handling
    print("❌ Connection Failed.")
    print(f"Error details: {e}")
