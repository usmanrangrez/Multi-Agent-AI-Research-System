from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from rich import print

load_dotenv()

writer_agent = create_agent(
    model="groq:openai/gpt-oss-120b",
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

def write_report(question: str, research_results: list[dict]):

    research_text = "\n\n".join(
        f"Source: {result['title']}\n"
        f"URL: {result['url']}\n"
        f"Findings:\n{result['findings']}"
        for result in research_results
    )

    print(f"[bold green]Writing research report for question:[/bold green] {question}")
    print(f"[bold blue]Research findings from sources:[/bold blue]\n{research_text}")

    writer_result = writer_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Research question: {question}\n\n"
                        f"Research findings from multiple sources:\n\n"
                        f"{research_text}"
                    ),
                }
            ]
        }
    )

    return writer_result
