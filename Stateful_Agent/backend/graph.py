from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from tools import weather_tool, dictionary_tool, web_search_tool
import os

# Load Gemini API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set in environment!")

# --------------------------------
# LLM
# --------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    api_key=api_key
)

# --------------------------------
# Tools
# --------------------------------
tools = [weather_tool, dictionary_tool, web_search_tool]
tool_node = ToolNode(tools)

# --------------------------------
# Assistant Node
# --------------------------------
def assistant_node(state: MessagesState):
    """
    LLM reasons over messages and may decide to call a tool.
    """
    # Use last messages
    last_messages = state["messages"]
    response = llm.invoke(last_messages)
    return {"messages": [response]}

# --------------------------------
# Conditional Routing
# --------------------------------
def route_tools(state: MessagesState):
    """
    Decide whether to call a tool or end the conversation.
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END

# --------------------------------
# Build Graph
# --------------------------------
graph = StateGraph(MessagesState)

graph.add_node("assistant", assistant_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "assistant")
graph.add_conditional_edges("assistant", route_tools)
graph.add_edge("tools", "assistant")

# Compile graph
app = graph.compile()
