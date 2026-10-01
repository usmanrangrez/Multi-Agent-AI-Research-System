from dotenv import load_dotenv
from langchain.agents import create_agent
from tools.search import search_web

load_dotenv()

search_agent = create_agent(
    model="google_genai:gemini-3.5-flash-lite",
    tools=[search_web],
    system_prompt=(
        "You are a research search agent."
        "When the user's question requires current or web-based information, "
        "use the search_web tool. "
        "Base your answer on the information returned by the tool."
    )
)
