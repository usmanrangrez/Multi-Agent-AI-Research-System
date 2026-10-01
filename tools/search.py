from config.settings import SEARCH_MAX_RESULTS
from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@tool
def search_web(query: str) -> list[dict]:
    """Search the web for current information about a topic."""

    search = TavilySearch(max_results=SEARCH_MAX_RESULTS)

    result = search.invoke({"query": query})

    return [
        {
            "title": item["title"],
            "url": item["url"],
            "content": item["content"],
        }
        for item in result["results"]
    ]