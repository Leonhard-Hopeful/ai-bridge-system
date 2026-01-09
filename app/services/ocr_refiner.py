from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1)

async def refine_ocr_text(raw_text: str):
    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Note Digitization Assistant. 
        Your task is to take messy OCR text from handwritten notes and:
        1. Correct spelling and grammar errors.
        2. Fix common OCR mistakes (e.g., '1' instead of 'I', '5' instead of 'S').
        3. Maintain the original structure and intent of the student's notes.
        4. Do NOT add new information. Only refine what is there."""),
        ("human", "Refine this raw OCR text:\n\n{text}")
    ])
    
    chain = refine_prompt | llm
    response = await chain.ainvoke({"text": raw_text})
    return response.content