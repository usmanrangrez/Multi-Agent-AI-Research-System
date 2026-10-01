from config.settings import CRITIC_MODEL
from dotenv import load_dotenv
from langchain.agents import create_agent
from prompts.critic import CRITIC_SYSTEM_PROMPT, build_critic_message
from schemas.critic import CriticResult

load_dotenv()

critic_agent = create_agent(
    model=CRITIC_MODEL,
    system_prompt=CRITIC_SYSTEM_PROMPT,
    response_format=CriticResult,
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
                    "content": build_critic_message(question, findings, report),
                }
            ]
        }
    )

    return critic_result["structured_response"]