import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


# Load environment variables

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set in environment!")


# Initialize FastAPI

app = FastAPI(title="Customer Support Chatbot API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize Gemini LLM

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # make sure this model exists
    api_key=api_key,
    temperature=0.3,
)


# System Prompt

SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are a helpful and polite customer support representative. "
        "You remember past messages and give clear, step-by-step help."
    )
)


# Chatbot Node

def support_agent(state: MessagesState):
    messages = state.get("messages", [])
    if not messages or messages[0].type != "system":
        messages = [SYSTEM_PROMPT] + messages

    try:
        response = llm.invoke(messages)
    except Exception as e:
        response = SystemMessage(content=f"Error generating response: {e}")

    return {"messages": messages + [response]}


# Build LangGraph with Memory

graph = StateGraph(MessagesState)
graph.add_node("support", support_agent)
graph.set_entry_point("support")
graph.set_finish_point("support")

memory = MemorySaver()
chat_app = graph.compile(checkpointer=memory)


# Request / Response Models

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    reply: str


# API Endpoints

@app.get("/ping")
def ping():
    """Simple health check"""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat endpoint linking frontend to LangGraph"""
    try:
        result = chat_app.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": str(request.thread_id)}},
        )
        reply = result["messages"][-1].content
    except Exception as e:
        reply = f"Error: {e}"
    return {"reply": reply}
