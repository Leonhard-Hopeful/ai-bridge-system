import os
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

# Initialize the "Brain"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Ensure the directory exists before connecting
persist_dir = "app/db/chroma_expert"
vector_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant",
    # Using your Groq API Key from environment variables
    api_key=os.getenv("GROQ_API_KEY") 
) 

async def stream_expert_response(user_message, subject):
    # 1. Search for chunks strictly related to the subject
    # 'k=4' ensures we get enough context for complex Simplex or Logic problems
    docs = vector_db.similarity_search(user_message, k=4, filter={"subject": subject})
    context = "\n---\n".join([d.page_content for d in docs])

    # 2. Your Specific "Strict" System Prompt (Unaltered)
    system_prompt_content = f"""
    ROLE: You are an elite tutor for {subject}.
    STRICT CONSTRAINT: Use ONLY the provided context to answer. 
    If the answer is not in the context, say: "This specific detail is not in your teacher's notes."
    
    STYLE RULES:
    - For Discrete Maths: Provide STEP-BY-STEP derivations.
    - For Operations Research: Use TABULAR methods for Simplex.
    - Match the notation and symbols found in the context exactly.

    When handling Stochastic Processes:
    1. Identify the State Space S = {{s1, s2, ...}}
    2. If the context provides a Transition Matrix P, represent it clearly in the response.
    3. If the user asks for a diagram, describe the nodes and edges based strictly on the provided text/matrix.


    CONTEXT FROM TEACHER'S NOTES:
    {context}
    """

    # 3. Stream the result using LangChain's astream
    messages = [
        SystemMessage(content=system_prompt_content),
        HumanMessage(content=user_message)
    ]

    try:
        async for chunk in llm.astream(messages):
            # Extract the text content from the chunk
            if chunk.content:
                yield chunk.content
    except Exception as e:
        print(f"Error streaming from Groq: {e}")
        yield "The expert system encountered an error while processing your request."