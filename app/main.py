from fastapi import FastAPI

# 1. Create the FastAPI instance
app = FastAPI(title="AI-Powered Learning Bridge")

# 2. Define your first 'Bridging' endpoint
@app.get("/")
async def read_root():
    """
    The landing page of your API. 
    It tells the user what the system is for.
    """
    return {
        "project": "AI-Powered Learning-to-Community Bridge",
        "objective": "Linking academic theory to real-world community challenges.",
        "status": "Online and ready to innovate!"
    }

# 3. An endpoint for a specific learning topic
@app.get("/bridge-topic/{topic_name}")
async def bridge_topic(topic_name: str):
    """
    This is where the 'Bridging Logic' will eventually live.
    For now, it returns a simple confirmation.
    """
    return {
        "topic": topic_name,
        "message": f"Successfully received the topic '{topic_name}'. We are ready to find community applications!"
    }