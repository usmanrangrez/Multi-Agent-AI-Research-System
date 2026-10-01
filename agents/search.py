from config.settings import SEARCH_MODEL
from dotenv import load_dotenv
from langchain.agents import create_agent
from prompts.search import SEARCH_SYSTEM_PROMPT
from tools.search import search_web

load_dotenv()

search_agent = create_agent(
    model=SEARCH_MODEL,
    tools=[search_web],
    system_prompt=SEARCH_SYSTEM_PROMPT,
)