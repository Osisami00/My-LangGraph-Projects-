from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
from datetime import datetime
import uuid

from config import config
from utils import (
    ensure_proper_punctuation, 
    extract_sources_from_response, 
    clean_response_text,
    extract_content_from_ai_message,
    check_if_retrieval_was_used
)
from document_processor import create_vector_store
from retriever import NelfundRetriever, nelfund_retriever
from agent import NelfundAgent

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ChatResponse(BaseModel):
    response: str
    session_id: str
    used_retrieval: bool = False
    sources: List[Dict] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    created_at: datetime

# Global instances
print("📚 NELFUND STUDENT LOAN NAVIGATOR")
print("✅ Importing dependencies...")

agent_instance = None
vectorstore_instance = None
nelfund_retriever_instance = None
sessions: Dict[str, Dict[str, Any]] = {}

def initialize_system():
    global agent_instance, vectorstore_instance, nelfund_retriever_instance
    
    print("\n🚀 Initializing NELFUND Assistant...")
    
    try:
        vectorstore_instance = create_vector_store()
        
        nelfund_retriever_instance = NelfundRetriever(vectorstore_instance)
        from retriever import nelfund_retriever as global_retriever
        global_retriever = nelfund_retriever_instance
        
        agent_instance = NelfundAgent()
        
        print("🎉 NELFUND Assistant is ready to help students!")
        print("\n📊 Configuration Summary:")
        print(f"   - Chat Model: Google Gemini {config.GEMINI_MODEL}")
        print(f"   - Embeddings: Sentence Transformer ({config.SENTENCE_TRANSFORMER_MODEL})")
        print(f"   - Vector Store: {config.VECTOR_STORE_PATH}")
        print(f"   - Document Chunks: Loaded from {len(config.DOCUMENT_PATHS)} sources")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        agent_instance = None

# Create FastAPI app
app = FastAPI(
    title="NELFUND Student Loan Navigator API",
    description="Intelligent AI Assistant for Nigerian Student Loan Guidance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    initialize_system()

@app.get("/")
async def root():
    return {
        "service": "NELFUND Student Loan Navigator",
        "status": "operational" if agent_instance else "initializing",
        "version": "1.0.0",
        "endpoints": ["/chat", "/sessions", "/reset", "/status", "/reload-embeddings"],
        "ai_provider": "Google Gemini AI (Chat) + Sentence Transformers (Embeddings)",
        "embedding_model": config.SENTENCE_TRANSFORMER_MODEL
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if agent_instance is None or agent_instance.agent is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    
    try:
        if request.session_id not in sessions:
            sessions[request.session_id] = {
                "created_at": datetime.now(),
                "messages": []
            }
        
        try:
            result = agent_instance.invoke(request.message, request.session_id)
        except Exception as agent_error:
            error_response = "I apologize, but I encountered an issue processing your request. This might be due to an out-of-context question or a system error. Please try rephrasing your question or asking about NELFUND student loans specifically."
            error_response = ensure_proper_punctuation(error_response)
            
            sessions[request.session_id]["messages"].extend([
                {"role": "user", "content": request.message, "timestamp": datetime.now()},
                {"role": "assistant", "content": error_response, "timestamp": datetime.now()}
            ])
            
            return ChatResponse(
                response=error_response,
                session_id=request.session_id,
                used_retrieval=False,
                sources=[]
            )
        
        final_response = None
        used_retrieval = check_if_retrieval_was_used(result)
        
        for message in result["messages"]:
            from langchain_core.messages import AIMessage
            if isinstance(message, AIMessage):
                response_content = extract_content_from_ai_message(message)
                if response_content:
                    cleaned_response = clean_response_text(response_content)
                    final_response = ensure_proper_punctuation(cleaned_response)
        
        if not final_response:
            final_response = "I apologize, I couldn't generate a response. Please try rephrasing your question or ask about NELFUND student loans specifically."
            final_response = ensure_proper_punctuation(final_response)
        
        sources = extract_sources_from_response(final_response)
        
        if used_retrieval and not sources:
            if not any('[Source:' in final_response or 'Source:' in final_response):
                used_retrieval = False
        
        sessions[request.session_id]["messages"].extend([
            {"role": "user", "content": request.message, "timestamp": datetime.now()},
            {"role": "assistant", "content": final_response, "timestamp": datetime.now()}
        ])
        
        return ChatResponse(
            response=final_response,
            session_id=request.session_id,
            used_retrieval=used_retrieval,
            sources=sources
        )
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        error_message = "I apologize, but I encountered an unexpected error. Please try again with a different question or contact support if the issue persists."
        error_message = ensure_proper_punctuation(error_message)
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)[:100]}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "created_at": sessions[session_id]["created_at"],
        "messages": sessions[session_id]["messages"],
        "message_count": len(sessions[session_id]["messages"])
    }

@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    if session_id in sessions:
        sessions[session_id]["messages"] = []
    return {"status": "session reset", "session_id": session_id}

@app.get("/status")
async def system_status():
    return {
        "status": "operational" if agent_instance else "error",
        "sessions_active": len(sessions),
        "total_messages": sum(len(s["messages"]) for s in sessions.values()),
        "vector_store": "loaded" if nelfund_retriever_instance else "not_loaded",
        "agent": "ready" if agent_instance else "not_ready",
        "ai_provider": "Google Gemini AI (Chat)",
        "embedding_model": config.SENTENCE_TRANSFORMER_MODEL,
        "cost_saving": "Yes - Sentence Transformers used for embeddings (no API calls)"
    }

@app.post("/reload-embeddings")
async def reload_embeddings():
    try:
        global vectorstore_instance, nelfund_retriever_instance
        vectorstore_instance = create_vector_store()
        nelfund_retriever_instance = NelfundRetriever(vectorstore_instance)
        from retriever import nelfund_retriever as global_retriever
        global_retriever = nelfund_retriever_instance
        return {"status": "success", "message": "Embeddings reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))