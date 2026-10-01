from config.settings import WRITER_MODEL
from dotenv import load_dotenv
from langchain.agents import create_agent
from prompts.writer import (
    WRITER_SYSTEM_PROMPT,
    build_writer_message,
    format_research,
)
from rich import print
from rich.markup import escape

load_dotenv()

writer_agent = create_agent(
    model=WRITER_MODEL,
    system_prompt=WRITER_SYSTEM_PROMPT,
)


def extract_report(writer_result: dict) -> str:
    final_message = writer_result["messages"][-1]
    return final_message.content


def write_report(
    question: str,
    research_results: list[dict],
    previous_report: str | None = None,
    critic_feedback: list[str] | None = None,
):
    research_text = format_research(research_results)

    # escape(): web text containing "[/x]" would crash rich's markup parser
    print(
        f"[bold green]Writing research report for question:[/bold green] "
        f"{escape(question)}"
    )
    print(
        f"[bold blue]Research findings from sources:[/bold blue]\n"
        f"{escape(research_text)}"
    )

    content = build_writer_message(
        question,
        research_text,
        previous_report=previous_report,
        critic_feedback=critic_feedback,
    )

    return writer_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        }
    )