# import os
# import asyncio
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain_community.tools import DuckDuckGoSearchRun
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough

# # -------------------------------------------------------------------
# # Environment setup
# # -------------------------------------------------------------------
# load_dotenv()
# if not os.getenv("GROQ_API_KEY"):
#     raise EnvironmentError(
#         "GROQ_API_KEY is not set. Please define it in your environment or .env file."
#     )

# # -------------------------------------------------------------------
# # Tooling & LLM
# # -------------------------------------------------------------------
# search_tool = DuckDuckGoSearchRun()

# llm = ChatGroq(
#     model="llama-3.1-8b-instant",
#     temperature=0.2,
# )

# # Bind tools to the LLM
# llm_with_tools = llm.bind_tools([search_tool])

# # -------------------------------------------------------------------
# # Prompt definition
# # -------------------------------------------------------------------
# prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are the AI Bridge Socratic Tutor in Cameroon.
# Your goal is to teach {topic} to a learner in {community}.

# RULES:
# - Explain only ONE small sub-concept at a time.
# - Use local analogies (e.g. comparing data to a market basket).
# - You MUST end every response with a question for the user.
# - If you need current information, you can use the search tool available to you."""),
#     MessagesPlaceholder(variable_name="chat_history", optional=True),
#     ("human", "{input}"),
# ])

# # -------------------------------------------------------------------
# # Session-scoped memory store
# # -------------------------------------------------------------------
# store: dict[str, InMemoryChatMessageHistory] = {}

# def get_session_history(session_id: str) -> BaseChatMessageHistory:
#     if session_id not in store:
#         store[session_id] = InMemoryChatMessageHistory()
#     return store[session_id]

# # -------------------------------------------------------------------
# # Chain factory with memory
# # -------------------------------------------------------------------
# def get_tutor_chain(topic: str, community: str):
#     # Inject topic and community into the prompt
#     partial_prompt = prompt.partial(topic=topic, community=community)
    
#     # Create the chain
#     chain = partial_prompt | llm_with_tools | StrOutputParser()
    
#     # Wrap with message history
#     chain_with_history = RunnableWithMessageHistory(
#         chain,
#         get_session_history,
#         input_messages_key="input",
#         history_messages_key="chat_history",
#     )
    
#     return chain_with_history

# # -------------------------------------------------------------------
# # Async execution wrapper
# # -------------------------------------------------------------------
# async def run_tutor_step(
#     session_id: str,
#     user_input: str,
#     topic: str,
#     community: str,
# ) -> str:
#     chain = get_tutor_chain(topic, community)
    
#     # Use ainvoke with session config
#     result = await chain.ainvoke(
#         {"input": user_input},
#         config={"configurable": {"session_id": session_id}},
#     )
    
#     return result


# # -------------------------------------------------------------------
# # Example usage
# # -------------------------------------------------------------------
# if __name__ == "__main__":
#     async def main():
#         session = "user123"
#         topic = "Python programming"
#         community = "Yaoundé"
        
#         # First interaction
#         response1 = await run_tutor_step(
#             session_id=session,
#             user_input="What is a variable?",
#             topic=topic,
#             community=community,
#         )
#         print("Response 1:", response1)
        
#         # Follow-up interaction (memory is preserved)
#         response2 = await run_tutor_step(
#             session_id=session,
#             user_input="Can you give me an example?",
#             topic=topic,
#             community=community,
#         )
#         print("\nResponse 2:", response2)
    
#     asyncio.run(main())
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

# Define the Enhanced Teaching Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the "AI Bridge Tutor," a brilliant and encouraging educator in Cameroon. 
    Your goal is to teach {topic} to a learner in {community}.

    ### CORE DIRECTIVES:
    1. **Brevity & Intuition**: Keep each response short and brief. Explain the "why" before the "how" using simple intuition.
    2. **Local Analogies**: Use Cameroonian references (e.g., "market woman logic," "taxi fare calculations," or "farming in the village").
    3. **Math & Science**: Use LaTeX for all formulas. 
       - Inline: Use $...$ (e.g., $E=mc^2$).
       - Block: Use $$...$$ (e.g., $$\\int_{{a}}^{{b}} f(x) dx$$).
       - IMPORTANT: For fractions, use double braces: $$\\frac{{numerator}}{{denominator}}$$.
    4. **Micro-Lessons**: Cover only ONE small sub-concept per turn. 
    5. **Socratic End**: Always end with ONE short, clear question.

    ### EXAMPLE FORMATTING:
    "If you have a fraction like $$\\frac{{1}}{{2}}$$, think of it as sharing one loaf of bread between two people in the quarter."
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])
# Memory Management
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# The Chain
chain = prompt | llm
runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

async def stream_tutor_response(user_input: str, topic: str, community: str, session_id: str):
    """Asynchronous generator that yields text chunks from the AI."""
    async for chunk in runnable_with_history.astream(
        {"input": user_input, "topic": topic, "community": community},
        config={"configurable": {"session_id": session_id}}
    ):
        if chunk.content:
            yield chunk.content