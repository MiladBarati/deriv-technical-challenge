import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GAPGPT_API_KEY")

if not api_key:
    print("Error: GAPGPT_API_KEY not found in .env file.")
else:
    # Initialize the client with the custom base URL and API key
    client = OpenAI(
        base_url='https://api.gapgpt.app/v1',
        api_key=api_key
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "سلام!"}
            ]
        )

        print("Response from GapGPT:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"An error occurred: {e}")
