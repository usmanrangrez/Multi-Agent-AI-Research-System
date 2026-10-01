from dotenv import load_dotenv
from langchain.agents import create_agent
from rich import print

load_dotenv()


writer_agent = create_agent(
    model="google_genai:gemini-3.5-flash-lite",
    system_prompt=(
        "You are a research writer agent. "
        "You will receive research findings collected from multiple sources. "
        "Synthesize the findings into a clear, structured research report. "
        "Use only the information provided in the research findings. "
        "Do not invent facts. "
        "When sources disagree or information is uncertain, make that clear."
    ),
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

    research_text = "\n\n".join(
        f"Source: {result['title']}\n"
        f"URL: {result['url']}\n"
        f"Findings:\n{result['findings']}"
        for result in research_results
    )

    # print(
    #     f"[bold green]Writing research report for question:[/bold green] "
    #     f"{question}"
    # )

    # print(
    #     f"[bold blue]Research findings from sources:[/bold blue]\n"
    #     f"{research_text}"
    # )

    if previous_report and critic_feedback:

        feedback_text = "\n".join(
            f"- {feedback}"
            for feedback in critic_feedback
        )

        content = (
            f"Research question: {question}\n\n"
            f"Research findings from multiple sources:\n\n"
            f"{research_text}\n\n"
            f"Previous draft:\n\n"
            f"{previous_report}\n\n"
            f"Critic feedback:\n\n"
            f"{feedback_text}\n\n"
            "Revise the previous draft using the critic feedback. "
            "Keep the useful parts of the previous draft, "
            "fix the identified problems, and use only the provided "
            "research findings."
        )

    else:

        content = (
            f"Research question: {question}\n\n"
            f"Research findings from multiple sources:\n\n"
            f"{research_text}"
        )

    writer_result = writer_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        }
    )

    return writer_result
