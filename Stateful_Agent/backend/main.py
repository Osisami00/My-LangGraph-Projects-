import re
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from graph import app as langgraph_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = langgraph_app.invoke({"messages": [HumanMessage(content=req.message)]})
        raw_reply = result["messages"][-1].content

        # Remove Markdown **bold**
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", raw_reply)

        # Replace newlines and bullet points with full stops
        cleaned = re.sub(r"[\n\*]+", ". ", cleaned)

        # Remove extra spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        return {"reply": cleaned}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"reply": f"⚠️ Internal error: {str(e)}"}
