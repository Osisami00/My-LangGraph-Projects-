import os
from typing import List, Any
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import config

def load_documents(file_paths: List[str]) -> List[Any]:
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
                
            docs = loader.load()
            documents.extend(docs)
            print(f"   → Loaded {len(docs)} pages/sections")
            
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
    
    return documents

def create_vector_store():
    print("\n🔧 Setting up vector database...")
    
    documents = load_documents(config.DOCUMENT_PATHS)
    
    if not documents:
        print("⚠️ No documents loaded. Creating sample data...")
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
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    
    splits = text_splitter.split_documents(documents)
    print(f"✅ Created {len(splits)} document chunks")
    
    print(f"🔍 Loading Sentence Transformer: {config.SENTENCE_TRANSFORMER_MODEL}")
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=config.SENTENCE_TRANSFORMER_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Sentence Transformer embeddings loaded successfully")
        
        test_text = "NELFUND student loan eligibility"
        test_embedding = embeddings.embed_query(test_text)
        print(f"   Embedding dimension: {len(test_embedding)}")
        
    except Exception as e:
        print(f"❌ Failed to load Sentence Transformer: {e}")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    print("💾 Creating vector store...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=config.VECTOR_STORE_PATH
    )
    
    print(f"✅ Vector store created at {config.VECTOR_STORE_PATH}")
    print(f"   Total documents: {len(splits)}")
    print(f"   Embedding model: {config.SENTENCE_TRANSFORMER_MODEL}")
    
    return vectorstore