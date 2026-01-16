import uvicorn
from api import app

if __name__ == "__main__":
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
    
    print("\n🔑 IMPORTANT: You need a GOOGLE_API_KEY environment variable for Gemini")
    print("   Get your API key from: https://makersuite.google.com/app/apikey")
    
    print("\n🔑 IMPORTANT: Update the config.py DOCUMENT_PATHS with your actual NELFUND files")
    print("📁 Place your documents in a 'data/' folder or update the paths")
    
    print("\n🧠 Sentence Transformer Model Info:")
    print("   Benefits: Local processing, no API costs, good quality embeddings")
    
    print("\n✨ MODULAR ARCHITECTURE:")
    print("  ✅ config.py - Configuration settings")
    print("  ✅ utils.py - Text processing utilities")
    print("  ✅ document_processor.py - Document loading and processing")
    print("  ✅ retriever.py - Document retrieval system")
    print("  ✅ agent.py - AI agent with LangGraph")
    print("  ✅ api.py - FastAPI endpoints")
    print("  ✅ main.py - Application entry point")
    
    print("\n🚀 Starting server on http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)