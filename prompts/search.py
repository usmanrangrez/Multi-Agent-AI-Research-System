SEARCH_SYSTEM_PROMPT = (
    "You are a research search agent. "
    "When the user's question requires current or web-based information, "
    "use the search_web tool. "
    "Base your answer on the information returned by the tool."
)


def search_user_message(question: str) -> str:
    return (
        "You MUST call the search_web tool to research "
        f"this question: {question}"
    )