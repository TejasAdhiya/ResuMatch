import os
from dotenv import load_dotenv
from openai import OpenAI

# Load your API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(prompt: str) -> str:
    try:
        print("=== SENDING PROMPT TO OPENAI ===")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        print(f"✅ OPENAI RESPONSE RECEIVED — Length: {len(content)}")
        return content
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        raise Exception("OpenAI request failed")