from config.settings import READER_MODEL
from dotenv import load_dotenv
from langchain.agents import create_agent
from prompts.reader import READER_SYSTEM_PROMPT
from tools.web_reader import read_webpage

load_dotenv()

reader_agent = create_agent(
    model=READER_MODEL,
    tools=[read_webpage],
    system_prompt=READER_SYSTEM_PROMPT,
)