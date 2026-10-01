WRITER_SYSTEM_PROMPT = (
    "You are a research writer agent. "
    "You will receive research findings collected from multiple sources. "
    "Synthesize the findings into a clear, structured research report. "
    "Use only the information provided in the research findings. "
    "Do not invent facts. "
    "When sources disagree or information is uncertain, make that clear."
)


def format_research(research_results: list[dict]) -> str:
    return "\n\n".join(
        f"Source: {result['title']}\n"
        f"URL: {result['url']}\n"
        f"Findings:\n{result['findings']}"
        for result in research_results
    )


def build_writer_message(
    question: str,
    research_text: str,
    previous_report: str | None = None,
    critic_feedback: list[str] | None = None,
) -> str:
    if previous_report and critic_feedback:
        feedback_text = "\n".join(f"- {feedback}" for feedback in critic_feedback)

        return (
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

    return (
        f"Research question: {question}\n\n"
        f"Research findings from multiple sources:\n\n"
        f"{research_text}"
    )