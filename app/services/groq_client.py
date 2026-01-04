import os
import asyncio # 1. Import asyncio
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def get_ai_bridging_stream(topic: str, community: str):
    prompt = (
        f"The user is learning about '{topic}'. They live in '{community}'. "
        f"Explain how this topic can solve a local problem in '{community}' "
        f"using local tools. Keep it practical and simple."
    )

    stream = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a community innovation mentor."},
            {"role": "user", "content": prompt}
        ],
        stream=True 
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
            # 2. Add a tiny delay (e.g., 0.05s for a typewriter effect)
            # 1 full second is actually very slow for reading!
            await asyncio.sleep(0.05)