import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def get_ai_bridging_stream(topic: str, community: str):
    """
    An async generator that yields chunks of text from Groq.
    """
    prompt = (
        f"The user is learning about '{topic}'. They live in '{community}'. "
        f"Explain how this topic can solve a local problem in '{community}' "
        f"using local tools. Keep it practical and simple."
    )

    # Note: we add 'stream=True' here
    stream = await client.chat.completions.create(
        model="llama3-8b-8192",
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