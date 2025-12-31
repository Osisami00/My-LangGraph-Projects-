from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv
from tools import weather_tool, dictionary_tool, web_search_tool
import os
from datetime import date


# Load environment

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set")


# LLM WITH TOOLS BOUND

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    api_key=api_key
)

tools = [weather_tool, dictionary_tool, web_search_tool]
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)


# Assistant Node

def assistant_node(state: MessagesState):
    """
    The LLM reasons and decides whether to call a tool.
    """
    messages = state["messages"]

    # Add system instruction ONCE
    if not any(m.type == "system" for m in messages):
        messages = [
            SystemMessage(
                content=(
                    f"You are a helpful AI assistant.\n"
                    f"Today's date is {date.today().strftime('%A, %B %d, %Y')}.\n\n"
                    "Rules:\n"
                    "- You may use the provided date for questions about today.\n"
                    "- Use the web search tool ONLY for news, events, or facts "
                    "that cannot be derived from the current date.\n"
                    "- Use tools when explicitly required.\n"
                    "- Do not guess weather or live data without tools."
                )
            )
        ] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Tool Routing
def route_tools(state: MessagesState):
    last_message = state["messages"][-1]

    # If the LLM requested tools → go to tool node
    if last_message.tool_calls:
        return "tools"

    return END


# Build Graph

graph = StateGraph(MessagesState)

graph.add_node("assistant", assistant_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "assistant")
graph.add_conditional_edges("assistant", route_tools)
graph.add_edge("tools", "assistant")

app = graph.compile()
