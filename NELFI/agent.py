from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from typing import Literal

from config import config
from retriever import retrieve_nelfund_info

class NelfundAgent:
    def __init__(self):
        self.llm = None
        self.llm_with_tools = None
        self.agent = None
        self.initialize_llm()
        if self.llm:
            self.create_agent()
    
    def initialize_llm(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL,
                temperature=0.3,
                google_api_key=config.GOOGLE_API_KEY,
                convert_system_message_to_human=True,
                max_output_tokens=2048,
                top_p=0.95,
                top_k=40,
            )
            print(f"✅ Gemini LLM initialized successfully with model: {config.GEMINI_MODEL}")
            
            tools = [retrieve_nelfund_info]
            self.llm_with_tools = self.llm.bind_tools(tools)
            
        except Exception as e:
            print(f"❌ Failed to initialize Gemini LLM: {e}")
            print("⚠️ Using Gemini requires GOOGLE_API_KEY environment variable")
            self.llm = None
            self.llm_with_tools = None
    
    def assistant_node(self, state: MessagesState) -> dict:
        if self.llm_with_tools is None:
            return {"messages": [AIMessage(content="I apologize, but the AI service is not available at the moment. Please check your API configuration.")]}
        
        system_prompt = SystemMessage(content=config.SYSTEM_PROMPT)
        messages = [system_prompt] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def should_retrieve(self, state: MessagesState) -> Literal["retrieve", "__end__"]:
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            if last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    if isinstance(tool_call, dict):
                        if tool_call.get('name') == 'retrieve_nelfund_info':
                            return "retrieve"
                    elif hasattr(tool_call, 'name'):
                        if tool_call.name == 'retrieve_nelfund_info':
                            return "retrieve"
        return "__end__"
    
    def create_agent(self):
        if self.llm is None:
            print("❌ Cannot create agent: LLM not initialized")
            return
        
        print("\n🧠 Building intelligent agent...")
        
        builder = StateGraph(MessagesState)
        
        builder.add_node("assistant", self.assistant_node)
        builder.add_node("retrieve", ToolNode([retrieve_nelfund_info]))
        
        builder.add_edge(START, "assistant")
        
        builder.add_conditional_edges(
            "assistant",
            self.should_retrieve,
            {
                "retrieve": "retrieve",
                "__end__": END
            }
        )
        
        builder.add_edge("retrieve", "assistant")
        
        memory = MemorySaver()
        self.agent = builder.compile(checkpointer=memory)
        
        print("✅ Agent created with conversation memory")
    
    def invoke(self, message: str, session_id: str):
        if self.agent is None:
            raise RuntimeError("Agent not initialized")
        
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": session_id}}
        )
        
        return result