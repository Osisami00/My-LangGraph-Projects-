from typing import List, Dict
from langchain_core.tools import tool

# Global retriever instance
nelfund_retriever = None

class NelfundRetriever:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        from config import config
        self.retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": config.RETRIEVAL_K,
                "fetch_k": config.RETRIEVAL_FETCH_K,
                "lambda_mult": 0.7
            }
        )
    
    def search(self, query: str) -> List[Dict]:
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

@tool
def retrieve_nelfund_info(query: str) -> str:
    """
    Retrieve relevant NELFUND student loan documents based on a user query.
    """
    global nelfund_retriever
    
    if nelfund_retriever is None:
        return "⚠️ Document database not initialized. Please restart the system."
    
    results = nelfund_retriever.search(query)
    
    if not results:
        return "🔍 No relevant documents found. Please try rephrasing your question."
    
    formatted_results = []
    for result in results:
        citation = f"[Source: {result['source']}, Page: {result['page']}]"
        formatted_results.append(
            f"📄 Document {result['id']}:\n{result['content']}\n{citation}\n"
        )
    
    return "\n" + "─" * 50 + "\n".join(formatted_results) + "\n" + "─" * 50