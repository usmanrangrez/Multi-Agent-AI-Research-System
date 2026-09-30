import json

from agents.reader import reader_agent
from agents.search import search_agent
from rich import print


def extract_sources(search_results: list[dict]) -> list[dict]:
    """Extract the useful source fields from search results."""

    return [
        {
            "title": result["title"],
            "url": result["url"],
        }
        for result in search_results
    ]


def run_research(question: str):
    # 1. Ask the Search Agent to find sources
    search_result = search_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    print("\nSEARCH RESULT:")
    print(search_result)

    # 2. Find the result produced by the search_web tool
    search_message = next(
        message
        for message in search_result["messages"]
        if getattr(message, "name", None) == "search_web"
    )

    print("\nSEARCH MESSAGE:")
    print(search_message)

    print("Type of search_message.content:", type(search_message.content))
    # 3. Convert the tool message back into Python data
    search_results = json.loads(search_message.content)

    # 4. Keep only the source information we need
    sources = extract_sources(search_results)

    print("\nSOURCES:")
    print(sources)

    # 5. Read the first source
    source = sources[0]

    reader_result = reader_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Research question: {question}\n\n"
                        f"Read this source:\n"
                        f"Title: {source['title']}\n"
                        f"URL: {source['url']}"
                    ),
                }
            ]
        }
    )

    return reader_result


if __name__ == "__main__":
    result = run_research(
        "What are the latest developments in RAG?"
    )

    print("\nREADER RESULT:")
    print(result)