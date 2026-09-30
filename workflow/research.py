import json

from agents.critic import critic_agent, critique_report
from agents.reader import reader_agent
from agents.search import search_agent
from agents.writer import extract_report, write_report
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


def read_source(question: str, source: dict):

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


def extract_findings(reader_result: dict) -> str:
    final_message = reader_result["messages"][-1]

    return final_message.content[0]["text"]


def run_research(question: str):

    # 1. Search
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

    # 2. Find search tool message
    search_message = next(
        message
        for message in search_result["messages"]
        if getattr(message, "name", None) == "search_web"
    )

    print("\nSEARCH MESSAGE:")
    print(search_message)

    # 3. Convert JSON → Python
    search_results = json.loads(search_message.content)

    # 4. Extract sources
    sources = extract_sources(search_results)

    print("\nSOURCES:")
    print(sources)

    # 5. Read sources
    reader_results = []

    for source in sources:
        print(f"\nREADING: {source['title']}")

        result = read_source(
            question,
            source,
        )

        findings = extract_findings(result)

        reader_results.append(
            {
                "title": source["title"],
                "url": source["url"],
                "findings": findings,
            }
        )

    # 6. Writer
    writer_result = write_report(
        question,
        reader_results,
    )

    report = extract_report(writer_result)

    # 7. Critic + revision loop
    max_revisions = 3

    for revision in range(max_revisions):

        critic_result = critique_report(
            question,
            reader_results,
            report,
        )

        print(f"\nCRITIC RESULT - Revision {revision}:")

        print(critic_result)

        if critic_result.approved:
            print("\nREPORT APPROVED")
            break

        print("\nREPORT REJECTED")
        print("Revising report...")

        writer_result = write_report(
            question,
            reader_results,
            previous_report=report,
            critic_feedback=critic_result.feedback,
        )

        report = extract_report(writer_result)

    return report

if __name__ == "__main__":
    results = run_research("What are the benefits of using CAG for LLMs?")

    print("\nFINAL RESEARCH REPORT:")
    print(results)
