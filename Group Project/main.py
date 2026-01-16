
"""
NELFUND STUDENT LOAN NAVIGATOR - AGENTIC RAG SYSTEM
Intelligent AI Assistant for Nigerian Student Loan Guidance
Author: AI Engineer
Date: 2024
"""

# ============================================================================
# IMPORTS
# ============================================================================
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# LangGraph/LangChain imports
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai

print("📚 NELFUND STUDENT LOAN NAVIGATOR")
print("✅ Importing dependencies...")

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================
load_dotenv()

# Configuration
class Config:
    # Document paths (YOU WILL UPDATE THESE)
    DOCUMENT_PATHS = [
        "data/FAQ-GENERAL-STAKEHOLDERS-AND-MEDIA.pdf",
        "data/FAQ-INSTITUTIONS.pdf", 
        "data/FAQ-PARENT-AND-GUARDIANS.pdf",
        "data/FAQ-STUDENTS.pdf",
        "data/Journal_2_25-pages-2.pdf",
        "data/NELFUND_FAQ.pdf",
        "data/NELFUND.pdf",
        "data/PUBLIC+GUIDELINES+FOR+APPLICANTS+FUND+UNDER+THE+STUDENTS+LOANS+ACT+2024.pdf",
        "data/Students-Loans-Access-to-Higher-Education-Act-2023.pdf"
    ]
    
    # Vector store
    VECTOR_STORE_PATH = "./nelfund_vectorstore"
    
    # Gemini Configuration (only for chat)
    GEMINI_MODEL = "gemini-1.5-pro"  # Changed to more stable model
    # Alternative: "gemini-1.5-flash" for faster/cheaper
    
    # Sentence Transformer Configuration
    SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Text splitting
    CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 200
    
    # Retrieval
    RETRIEVAL_K = 5
    RETRIEVAL_FETCH_K = 10

config = Config()

# ============================================================================
# DOCUMENT PROCESSING PIPELINE
# ============================================================================
def load_documents(file_paths: List[str]) -> List[Any]:
    """
    Load documents from various file types.
    Returns a list of Document objects.
    """
    documents = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: File not found - {file_path}")
            continue
            
        try:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                print(f"📄 Loading PDF: {file_path}")
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
                print(f"📝 Loading text: {file_path}")
            elif file_path.endswith('.csv'):
                loader = CSVLoader(file_path)
                print(f"📊 Loading CSV: {file_path}")
            elif file_path.endswith('.md'):
                loader = UnstructuredMarkdownLoader(file_path)
                print(f"📋 Loading markdown: {file_path}")
            else:
                print(f"❓ Unsupported format: {file_path}")
                continue
                
            # Load documents
            docs = loader.load()
            documents.extend(docs)
            print(f"   → Loaded {len(docs)} pages/sections")
            
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
    
    return documents

def create_vector_store():
    """
    Create and populate the vector database using Sentence Transformers.
    This should be run once during initialization.
    """
    print("\n🔧 Setting up vector database...")
    
    # 1. Load documents
    documents = load_documents(config.DOCUMENT_PATHS)
    
    if not documents:
        print("⚠️ No documents loaded. Creating sample data...")
        # Create sample documents for demonstration
        from langchain_core.documents import Document
        
        documents = [
            Document(
                page_content="""NELFUND (Student Loans Act 2023) provides interest-free loans to Nigerian students.
                Eligibility Criteria:
                1. Admission into a public Nigerian university, polytechnic, or college of education
                2. Family income below ₦500,000 per annum
                3. Guarantor required (civil servant level 12 or above)
                4. No age limit""",
                metadata={"source": "eligibility_guidelines.pdf", "page": 1}
            ),
            Document(
                page_content="""Application Process:
                1. Register on NELFUND portal with JAMB registration number
                2. Submit required documents (admission letter, income statement, guarantor form)
                3. Wait for verification (4-6 weeks)
                4. Receive disbursement directly to institution""",
                metadata={"source": "application_procedure.pdf", "page": 2}
            )
        ]
    
    # 2. Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    
    splits = text_splitter.split_documents(documents)
    print(f"✅ Created {len(splits)} document chunks")
    
    # 3. Create embeddings using Sentence Transformers
    print(f"🔍 Loading Sentence Transformer: {config.SENTENCE_TRANSFORMER_MODEL}")
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=config.SENTENCE_TRANSFORMER_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Sentence Transformer embeddings loaded successfully")
        
        # Test the embeddings
        test_text = "NELFUND student loan eligibility"
        test_embedding = embeddings.embed_query(test_text)
        print(f"   Embedding dimension: {len(test_embedding)}")
        
    except Exception as e:
        print(f"❌ Failed to load Sentence Transformer: {e}")
        print("⚠️ Using default embeddings as fallback")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    # 4. Create vector store
    print("💾 Creating vector store...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=config.VECTOR_STORE_PATH
    )
    
    # vectorstore.persist()
    print(f"✅ Vector store created at {config.VECTOR_STORE_PATH}")
    print(f"   Total documents: {len(splits)}")
    print(f"   Embedding model: {config.SENTENCE_TRANSFORMER_MODEL}")
    
    return vectorstore

# ============================================================================
# RETRIEVAL TOOL
# ============================================================================
class NelfundRetriever:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": config.RETRIEVAL_K,
                "fetch_k": config.RETRIEVAL_FETCH_K,
                "lambda_mult": 0.7
            }
        )
    
    def search(self, query: str) -> List[Dict]:
        """Search for relevant documents"""
        docs = self.retriever.invoke(query)
        
        results = []
        for i, doc in enumerate(docs):
            results.append({
                "id": i + 1,
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "N/A")
            })
        
        return results

# Create retrieval tool
nelfund_retriever = None

@tool
def retrieve_nelfund_info(query: str) -> str:
    """
    Search NELFUND policy documents for specific information.
    
    USE THIS TOOL WHEN:
    - User asks about eligibility criteria
    - User asks about application process
    - User asks about repayment terms
    - User asks about required documents
    - User asks about covered institutions
    - User asks specific policy questions
    
    DO NOT USE WHEN:
    - User says hello or goodbye
    - User asks about your capabilities
    - Simple yes/no questions already in context
    
    Returns formatted document excerpts with citations.
    """
    global nelfund_retriever
    
    if nelfund_retriever is None:
        return "⚠️ Document database not initialized. Please restart the system."
    
    results = nelfund_retriever.search(query)
    
    if not results:
        return "🔍 No relevant documents found. Please try rephrasing your question."
    
    # Format results with citations
    formatted_results = []
    for result in results:
        citation = f"[Source: {result['source']}, Page: {result['page']}]"
        formatted_results.append(
            f"📄 Document {result['id']}:\n{result['content']}\n{citation}\n"
        )
    
    return "\n" + "─" * 50 + "\n".join(formatted_results) + "\n" + "─" * 50

# ============================================================================
# AGENTIC RAG SYSTEM (LangGraph)
# ============================================================================
# Initialize Gemini LLM for chat only
try:
    # Configure Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        temperature=0.3,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True,
        max_output_tokens=2048,
        top_p=0.95,
        top_k=40
    )
    print(f"✅ Gemini LLM initialized successfully with model: {config.GEMINI_MODEL}")
except Exception as e:
    print(f"❌ Failed to initialize Gemini LLM: {e}")
    print("⚠️ Using Gemini requires GOOGLE_API_KEY environment variable")
    print("   Get your API key from: https://makersuite.google.com/app/apikey")
    llm = None

# System prompt for NELFUND specialist
SYSTEM_PROMPT = SystemMessage(content="""You are NELFI - the NELFUND Student Loan Navigator AI.

MISSION: Help Nigerian students understand and access student loans through NELFUND.

RETRIEVAL DECISION RULES:

ALWAYS RETRIEVE DOCUMENTS FOR:
1. Eligibility questions: "Am I eligible?", "Who can apply?", "Income requirements"
2. Application process: "How do I apply?", "What documents?", "Application steps"
3. Repayment questions: "When to repay?", "Interest rate?", "Repayment period"
4. Policy details: "What courses are covered?", "Which institutions?", "Loan limits"
5. Specific requirements: "Do I need a guarantor?", "What if I fail a course?"

ANSWER DIRECTLY FOR:
1. Greetings: "Hello", "Hi", "Good morning"
2. Capabilities: "What can you do?", "How do you work?"
3. Simple follow-ups: If answer is already in conversation context
4. General encouragement: "Thank you", "You're helpful"

RESPONSE GUIDELINES:
- ALWAYS cite sources when using retrieved information
- Be empathetic - students are anxious about their education
- Provide clear step-by-step guidance when possible
- If unsure, say so and suggest official channels
- Use Nigerian context (mention Naira amounts, Nigerian institutions)

IMPORTANT: When user asks about eligibility, always ask follow-up questions:
1. "Have you been admitted to a public institution?"
2. "What is your family's annual income?"
3. "Do you have a potential guarantor?"

Start by introducing yourself and asking how you can help.
""")

# Bind tools to LLM
tools = [retrieve_nelfund_info]
if llm:
    llm_with_tools = llm.bind_tools(tools)
else:
    llm_with_tools = None

def assistant_node(state: MessagesState) -> dict:
    """Main assistant node - decides whether to retrieve"""
    if llm_with_tools is None:
        return {"messages": [AIMessage(content="I apologize, but the AI service is not available at the moment. Please check your API configuration.")]}
    
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_retrieve(state: MessagesState) -> Literal["retrieve", "__end__"]:
    """Routing function - decide tool use"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "retrieve"
    return "__end__"

# Build the graph
def create_agent():
    """Create and compile the LangGraph agent"""
    print("\n🧠 Building intelligent agent...")
    
    if llm is None:
        print("❌ Cannot create agent: LLM not initialized")
        return None
    
    builder = StateGraph(MessagesState)
    
    # Add nodes
    builder.add_node("assistant", assistant_node)
    builder.add_node("retrieve", ToolNode(tools))
    
    # Add edges
    builder.add_edge(START, "assistant")
    
    builder.add_conditional_edges(
        "assistant",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "__end__": END
        }
    )
    
    builder.add_edge("retrieve", "assistant")
    
    # Add memory for conversation continuity
    memory = MemorySaver()
    agent = builder.compile(checkpointer=memory)
    
    print("✅ Agent created with conversation memory")
    return agent

# ============================================================================
# FASTAPI BACKEND
# ============================================================================
app = FastAPI(
    title="NELFUND Student Loan Navigator API",
    description="Intelligent AI Assistant for Nigerian Student Loan Guidance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Helper function to extract content from AIMessage
def extract_content_from_ai_message(message) -> str:
    """Extract content from AI message, handling different formats"""
    if isinstance(message.content, str):
        return message.content
    elif isinstance(message.content, list):
        # Handle list format (Gemini sometimes returns list of content blocks)
        content_parts = []
        for item in message.content:
            if hasattr(item, 'text'):
                content_parts.append(item.text)
            elif isinstance(item, dict) and 'text' in item:
                content_parts.append(item['text'])
            elif isinstance(item, str):
                content_parts.append(item)
        return " ".join(content_parts)
    elif hasattr(message, 'content'):
        # Try to convert to string
        return str(message.content)
    else:
        return "I couldn't generate a response. Please try again."

# Session management
sessions = {}

# Initialize agent
print("\n🚀 Initializing NELFUND Assistant...")
try:
    vectorstore = create_vector_store()
    nelfund_retriever = NelfundRetriever(vectorstore)
    agent = create_agent()
    print("🎉 NELFUND Assistant is ready to help students!")
    print("\n📊 Configuration Summary:")
    print(f"   - Chat Model: Google Gemini {config.GEMINI_MODEL}")
    print(f"   - Embeddings: Sentence Transformer ({config.SENTENCE_TRANSFORMER_MODEL})")
    print(f"   - Vector Store: {config.VECTOR_STORE_PATH}")
    print(f"   - Document Chunks: Loaded from {len(config.DOCUMENT_PATHS)} sources")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    agent = None

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "NELFUND Student Loan Navigator",
        "status": "operational" if agent else "initializing",
        "version": "1.0.0",
        "endpoints": ["/chat", "/sessions", "/reset"],
        "ai_provider": "Google Gemini AI (Chat) + Sentence Transformers (Embeddings)",
        "embedding_model": config.SENTENCE_TRANSFORMER_MODEL
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    
    try:
        # Get or create session
        if request.session_id not in sessions:
            sessions[request.session_id] = {
                "created_at": datetime.now(),
                "messages": []
            }
        
        # Invoke agent
        result = agent.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.session_id}}
        )
        
        # Extract response
        final_response = None
        used_retrieval = False
        sources = []
        
        for message in result["messages"]:
            if isinstance(message, AIMessage):
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    used_retrieval = True
                
                # Extract content properly
                final_response = extract_content_from_ai_message(message)
        
        # If no response extracted, create a default
        if not final_response:
            final_response = "I apologize, I couldn't generate a response. Please try rephrasing your question."
        
        # Update session history
        sessions[request.session_id]["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now()
        })
        
        sessions[request.session_id]["messages"].append({
            "role": "assistant",
            "content": final_response,
            "timestamp": datetime.now()
        })
        
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session"""
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
    """Reset a conversation session"""
    if session_id in sessions:
        sessions[session_id]["messages"] = []
    return {"status": "session reset", "session_id": session_id}

@app.get("/status")
async def system_status():
    """System status and statistics"""
    return {
        "status": "operational" if agent else "error",
        "sessions_active": len(sessions),
        "total_messages": sum(len(s["messages"]) for s in sessions.values()),
        "vector_store": "loaded" if nelfund_retriever else "not_loaded",
        "agent": "ready" if agent else "not_ready",
        "ai_provider": "Google Gemini AI (Chat)",
        "embedding_model": config.SENTENCE_TRANSFORMER_MODEL,
        "cost_saving": "Yes - Sentence Transformers used for embeddings (no API calls)"
    }

@app.post("/reload-embeddings")
async def reload_embeddings():
    """Reload the vector store with updated documents"""
    try:
        global vectorstore, nelfund_retriever
        vectorstore = create_vector_store()
        nelfund_retriever = NelfundRetriever(vectorstore)
        return {"status": "success", "message": "Embeddings reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DEBUG ENDPOINT - FOR TESTING GEMINI RESPONSE FORMAT
# ============================================================================
@app.post("/debug-gemini")
async def debug_gemini(message: str):
    """Debug endpoint to see Gemini response format"""
    try:
        test_messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=message)
        ]
        
        response = llm.invoke(test_messages)
        
        return {
            "raw_response": str(response),
            "response_type": type(response).__name__,
            "content_type": type(response.content).__name__,
            "content_value": response.content,
            "has_tool_calls": hasattr(response, 'tool_calls'),
            "tool_calls": getattr(response, 'tool_calls', None),
            "extracted_content": extract_content_from_ai_message(response)
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🖥️  FASTAPI SERVER STARTING")
    print("="*60)
    print("\n📚 Available endpoints:")
    print("  • GET  /              - Health check")
    print("  • POST /chat          - Chat with NELFUND assistant")
    print("  • GET  /sessions/{id} - Get conversation history")
    print("  • POST /reset/{id}    - Reset session")
    print("  • GET  /status        - System status")
    print("  • POST /reload-embeddings - Update document embeddings")
    print("  • POST /debug-gemini  - Debug Gemini response format")
    
    print("\n🔑 IMPORTANT: You need a GOOGLE_API_KEY environment variable for Gemini")
    print("   Get your API key from: https://makersuite.google.com/app/apikey")
    print("   Note: Embeddings use local Sentence Transformers - NO API COST! ✅")
    
    print("\n🔑 IMPORTANT: Update the Config.DOCUMENT_PATHS with your actual NELFUND files")
    print("📁 Place your documents in a 'data/' folder or update the paths")
    
    print("\n🧠 Sentence Transformer Model Info:")
    print(f"   Model: {config.SENTENCE_TRANSFORMER_MODEL}")
    print("   Benefits: Local processing, no API costs, good quality embeddings")
    
    print("\n🚀 Starting server on http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)