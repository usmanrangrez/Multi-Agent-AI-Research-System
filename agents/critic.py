from dotenv import load_dotenv
from langchain.agents import create_agent
from rich import print
from schemas.critic import CriticResult

load_dotenv()



critic_agent = create_agent(
    model="groq:openai/gpt-oss-120b",
    system_prompt=(
        "You are a research critic agent. "
        "Your job is to evaluate a research draft for accuracy, "
        "completeness, clarity, and support from the provided research findings. "
        "\n\n"
        "Check whether the draft is consistent with the research findings. "
        "Identify unsupported claims, missing important information, "
        "contradictions, and unclear statements. "
        "\n\n"
        "Do not rewrite the draft. "
        "Instead, provide clear feedback that another writer agent can use "
        "to improve the draft. "
        "\n\n"
        "At the end, clearly state whether the draft is approved."
    ),
    response_format=CriticResult
)

def critique_report(
    question: str,
    findings: list[dict],
    report: str,
):
    critic_result = critic_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Research question: {question}\n\n"
                        f"Research findings:\n{findings}\n\n"
                        f"Draft report:\n{report}\n\n"
                        "Evaluate the draft report against the research findings."
                    ),
                }
            ]
        }
    )

    return critic_result["structured_response"]


    draft = """
    RAG combines retrieval with generation.
    It allows an LLM to use external information when answering questions.
    """

    findings = """
    RAG systems retrieve relevant documents and provide them as context
    to a language model before generation.
    """

    prompt = f"""
    Research findings:

    {findings}

    Draft:

    {draft}

    Evaluate the draft against the research findings.
    """

    result = critic_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }
    )

    critic_result = result["structured_response"]

    print(critic_result)    