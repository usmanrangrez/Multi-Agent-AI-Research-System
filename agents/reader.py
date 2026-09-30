from dotenv import load_dotenv
from langchain.agents import create_agent
from tools.web_reader import read_webpage

load_dotenv()
reader_agent = create_agent(
    model="groq:openai/gpt-oss-20b",
    tools=[read_webpage],
    system_prompt=(
        "You are a research reader agent. "
        "When given a webpage URL, use the read_webpage tool "
        "to retrieve the webpage content. "
        "Extract the information relevant to the user's research question. "
        "Do not invent information that is not present in the webpage."
    ),
)