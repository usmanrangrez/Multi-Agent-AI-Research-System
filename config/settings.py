"""Central settings. Change models, limits and defaults here, not inside agent files."""

import os

from dotenv import load_dotenv

load_dotenv()

# Models 
# One default for everything; override per agent via .env or by editing below.
DEFAULT_MODEL = os.getenv("RESEARCH_MODEL", "google_genai:gemini-3.5-flash-lite")

SEARCH_MODEL = os.getenv("SEARCH_MODEL", DEFAULT_MODEL)
READER_MODEL = os.getenv("READER_MODEL", DEFAULT_MODEL)
WRITER_MODEL = os.getenv("WRITER_MODEL", DEFAULT_MODEL)
CRITIC_MODEL = os.getenv("CRITIC_MODEL", DEFAULT_MODEL)  

# Search 
SEARCH_MAX_RESULTS = 5

#  Reader 
READER_TIMEOUT_SECONDS = 10
READER_MAX_CHARS = 15_000          # cap page text so prompts don't explode
READER_USER_AGENT = "Mozilla/5.0"

# Pipeline
DEFAULT_MAX_REVISIONS = 3          # critic rounds (UI slider default)
RETRY_ATTEMPTS = 4                 # for transient API/network errors