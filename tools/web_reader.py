import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
def read_webpage(url: str) -> str:
    """Fetch a webpage and extract its readable text."""

    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup.find_all(
        ["script", "style", "nav", "footer", "header"]
    ):
        element.decompose()

    text = soup.get_text(
        separator="\n",
        strip=True,
    )

    return text