import json
import time
from typing import Callable

from agents.critic import critique_report
from agents.reader import reader_agent
from agents.search import search_agent
from agents.writer import extract_report, write_report
from config.settings import DEFAULT_MAX_REVISIONS, RETRY_ATTEMPTS
from prompts.critic import STRICT_REVIEW_POLICY
from prompts.reader import reader_user_message
from prompts.search import search_user_message
from tools.search import search_web

EventCallback = Callable[[dict], None]



# ============================================================
# HELPERS
# ============================================================

def to_text(content) -> str:
    """Flatten LangChain content (str / list of blocks / message) into plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        if "content" in content:
            return to_text(content["content"])
        return ""
    if isinstance(content, (list, tuple)):
        parts = (to_text(item) for item in content)
        return "\n\n".join(part for part in parts if part)
    if hasattr(content, "content"):
        return to_text(content.content)
    return str(content)


def emit(on_event: EventCallback | None, event_type: str, **data) -> None:
    """Send a progress event to the UI. Never lets a UI problem break the pipeline."""
    if on_event is None:
        return
    try:
        on_event({"type": event_type, **data})
    except Exception:
        pass


TRANSIENT_MARKERS = (
    "remoteprotocolerror", "server disconnected", "connecterror", "connection",
    "readtimeout", "timeout", "timed out", "503", "502", "500", "429",
    "unavailable", "overloaded", "resource_exhausted", "rate limit",
)


def with_retry(func, *args, step: str, on_event=None, attempts: int = RETRY_ATTEMPTS, **kwargs):
    """Call func(*args, **kwargs); retry transient network/API errors with backoff."""
    for attempt in range(1, attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            text = f"{type(error).__name__} {error}".lower()
            transient = any(marker in text for marker in TRANSIENT_MARKERS)
            if not transient or attempt == attempts:
                raise
            wait = 2 ** attempt  # 2s, 4s, 8s
            emit(on_event, "retry", step=step, attempt=attempt, max=attempts, wait=wait)
            time.sleep(wait)


# ============================================================
# SEARCH
# ============================================================

def parse_search_results(search_result: dict) -> list[dict] | None:
    """Pull the search_web tool output out of the agent's messages (None if not found)."""
    for message in search_result.get("messages", []):
        if getattr(message, "name", None) != "search_web":
            continue

        content = message.content
        if not isinstance(content, str):
            content = to_text(content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue

        if isinstance(data, list) and data:
            return data

    return None


def search_sources(question: str, on_event: EventCallback | None) -> list[dict]:
    """Run the search agent. If the model skips the tool, call the tool directly."""
    results = None

    try:
        search_result = search_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": search_user_message(question),
                    }
                ]
            }
        )
        results = parse_search_results(search_result)
    except Exception as error:
        print(f"Search agent failed ({type(error).__name__}: {error})")

    if not results:
        emit(on_event, "search_fallback")
        results = with_retry(
            search_web.invoke, {"query": question}, step="search", on_event=on_event
        )

    if not results:
        raise RuntimeError("The web search returned no results.")

    return results


def extract_sources(search_results: list[dict]) -> list[dict]:
    """Keep title + url and drop duplicate URLs."""
    seen = set()
    sources = []

    for result in search_results:
        url = result.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(
            {
                "title": result.get("title") or url,
                "url": url,
            }
        )

    return sources


# ============================================================
# READER
# ============================================================

def read_source(question: str, source: dict) -> dict:
    return reader_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": reader_user_message(question, source),
                }
            ]
        }
    )


def extract_findings(reader_result: dict) -> str:
    return to_text(reader_result["messages"][-1].content).strip()


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_research(
    question: str,
    on_event: EventCallback | None = None,
    max_revisions: int = DEFAULT_MAX_REVISIONS,
    strict_critic: bool = False,
) -> dict:
    """Search -> Read -> Write -> Critic loop.

    Returns {"report": str, "sources": [...], "findings": [...]}.
    """

    max_revisions = max(1, int(max_revisions))
    review_question = (
        f"{question}\n\n{STRICT_REVIEW_POLICY}" if strict_critic else question
    )

    # 1. Search
    emit(on_event, "search_start")
    search_results = search_sources(question, on_event)
    sources = extract_sources(search_results)
    emit(on_event, "search_done", n=len(sources), sources=sources)

    # 2. Read every source (one bad page must not kill the run)
    emit(on_event, "read_start")
    reader_results = []

    for index, source in enumerate(sources, start=1):
        emit(
            on_event,
            "read_progress",
            i=index,
            total=len(sources),
            title=source["title"],
        )

        try:
            findings = extract_findings(
                with_retry(read_source, question, source, step="read", on_event=on_event)
            )
        except Exception as error:
            emit(
                on_event,
                "source_failed",
                title=source["title"],
                reason=f"{type(error).__name__}: {error}",
            )
            continue

        if not findings:
            emit(
                on_event,
                "source_failed",
                title=source["title"],
                reason="empty findings",
            )
            continue

        reader_results.append(
            {
                "title": source["title"],
                "url": source["url"],
                "findings": findings,
            }
        )

    if not reader_results:
        raise RuntimeError("None of the sources could be read.")

    emit(on_event, "read_done", n=len(reader_results))

    # 3. Write the first draft
    emit(on_event, "write_start", round=1)
    writer_result = with_retry(
        write_report, question, reader_results, step="write", on_event=on_event
    )
    report = to_text(extract_report(writer_result)).strip()
    emit(on_event, "write_done", round=1)

    # 4. Critic + revision loop
    for round_number in range(1, max_revisions + 1):
        emit(on_event, "critic_start")
        critic_result = with_retry(
            critique_report, review_question, reader_results, report,
            step="critic", on_event=on_event,
        )

        if critic_result.approved:
            emit(on_event, "critic_done", approved=True)
            break

        if round_number == max_revisions:
            emit(on_event, "critic_done", approved=False)
            break

        next_round = round_number + 1
        emit(
            on_event,
            "critic_revision",
            round=next_round,
            feedback="; ".join(critic_result.feedback),
        )

        emit(on_event, "write_start", round=next_round)
        writer_result = with_retry(
            write_report,
            question,
            reader_results,
            previous_report=report,
            critic_feedback=critic_result.feedback,
            step="write",
            on_event=on_event,
        )
        report = to_text(extract_report(writer_result)).strip()
        emit(on_event, "write_done", round=next_round)

    return {
        "report": report,
        "sources": sources,
        "findings": reader_results,
    }


if __name__ == "__main__":
    output = run_research(
        "What are the benefits of using CAG for LLMs?",
        on_event=lambda event: print("EVENT:", event),
    )

    print("\nFINAL RESEARCH REPORT:\n")
    print(output["report"])