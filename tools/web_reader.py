import requests
from bs4 import BeautifulSoup
from config.settings import (
    READER_MAX_CHARS,
    READER_TIMEOUT_SECONDS,
    READER_USER_AGENT,
)
from langchain_core.tools import tool


@tool
def read_webpage(url: str) -> str:
    """Fetch a webpage and extract its readable text."""

    try:
        response = requests.get(
            url,
            timeout=READER_TIMEOUT_SECONDS,
            headers={"User-Agent": READER_USER_AGENT},
        )
        response.raise_for_status()

    except requests.RequestException as error:
        return f"Unable to read webpage: {url}\nReason: {error}"

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup.find_all(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)

    return text[:READER_MAX_CHARS]