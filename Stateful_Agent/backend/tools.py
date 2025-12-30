from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def weather_tool(city: str) -> str:
    """Get simulated weather for a city."""  # <-- THIS DOCSTRING IS REQUIRED
    fake_weather = {
        "lagos": "Sunny, 32°C",
        "london": "Cloudy, 18°C",
        "new york": "Rainy, 22°C",
    }
    return fake_weather.get(city.lower(), "Weather data not available")

@tool
def dictionary_tool(word: str) -> str:
    """Get definition of a word."""  
    dictionary = {
        "ephemeral": "Lasting for a very short time.",
        "agent": "An entity that perceives and acts upon its environment.",
    }
    return dictionary.get(word.lower(), "Definition not found.")

@tool
def web_search_tool(query: str) -> str:
    """Search the web using DuckDuckGo."""  
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        summaries = [r["body"] for r in results]
        return "\n".join(summaries) if summaries else "No results found."
