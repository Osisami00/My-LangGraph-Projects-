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
        result = langgraph_app.invoke(
            {"messages": [HumanMessage(content=req.message)]}
        )

        last_msg = result["messages"][-1]
        content = last_msg.content

        
        # FIX: Normalize content to string
        
        if isinstance(content, list):
            # Gemini sometimes returns structured content
            content = " ".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )

        if not isinstance(content, str):
            content = str(content)

        
        # formatting output
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
        cleaned = re.sub(r"[\n•*-]+", ". ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        return {"reply": cleaned}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"reply": f"Internal error: {str(e)}"}
