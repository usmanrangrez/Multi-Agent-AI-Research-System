from pprint import pprint

from agents.search import search_agent

result = search_agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What are the ways to earn money by using AI in 2026?"
            }
        ]
    }
)

pprint(result)