from langchain_core.tools import tool
from duckduckgo_search import DDGS
from datetime import datetime

# -------------------------------
# Weather Tool (Explicitly Simulated)
# -------------------------------
@tool
def weather_tool(city: str) -> str:
    """
    Get simulated weather for a city.
    This tool does NOT provide real-time weather.
    """
    print("WEATHER TOOL CALLED:", city)

    fake_weather = {
        "lagos": "Sunny, 32°C",
        "london": "Cloudy, 18°C",
        "new york": "Rainy, 22°C",
    }

    weather = fake_weather.get(city.lower())
    if not weather:
        return (
            f"No simulated weather data available for {city}. "
            "Real-time weather is not supported."
        )

    return f"Simulated weather for {city.title()}: {weather}"

# -----------------------------
# Dictionary Tool

@tool
def dictionary_tool(word: str) -> str:
    """
    Look up the definition of a word from a small dictionary.
    """
    print("DICTIONARY TOOL CALLED:", word)

    dictionary = {
        "ephemeral": "Lasting for a very short time.",
        "agent": "An entity that perceives and acts upon its environment.",
        "dismal": "Gloomy, depressing, or lacking in hope."
    }

    definition = dictionary.get(word.lower())
    if not definition:
        return f"No definition found for '{word}'."

    return f"Definition of '{word}': {definition}"

# -------------------------------
# Web Search Tool (DuckDuckGo)
# -------------------------------
@tool
def web_search_tool(query: str) -> str:
    """
    Search the web using DuckDuckGo.
    Use this tool for current events, dates, or real-world facts.
    """
    print("DUCKDUCKGO TOOL CALLED:", query)

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))

    if not results:
        return "No search results found."

    summaries = []
    for r in results:
        body = r.get("body", "")
        source = r.get("href", "")
        if body:
            summaries.append(f"{body} (source: {source})")

    return "\n\n".join(summaries)
