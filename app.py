import html
import queue
import re
import textwrap
import threading
import time
import traceback

import streamlit as st
from config.settings import DEFAULT_MAX_REVISIONS
from workflow.research import run_research

# ============================================================
# PAGE CONFIG  (must be the first Streamlit command)
# ============================================================

st.set_page_config(
    page_title="Researcher — Multi-Agent AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

    /* NOTE: never target bare `span`/`div` fonts — Streamlit icons are spans
       using the Material Symbols font and would turn into literal text. */
    .stApp {
        font-family: 'Inter', sans-serif;
        background:
            radial-gradient(ellipse 60% 45% at 12% -5%, rgba(99,102,241,0.22), transparent 60%),
            radial-gradient(ellipse 45% 40% at 95% 10%, rgba(14,165,233,0.16), transparent 60%),
            radial-gradient(ellipse 40% 35% at 50% 110%, rgba(168,85,247,0.10), transparent 60%),
            #060a13;
        color: #e2e8f0;
    }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 5rem; }
    h1, h2, h3, p, label, button, textarea, input { font-family: 'Inter', sans-serif; }
    ::selection { background: rgba(99,102,241,0.4); }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #0a0f1c; }
    ::-webkit-scrollbar-thumb { background: #26334d; border-radius: 6px; }

    /* ---------- SIDEBAR ---------- */
    section[data-testid="stSidebar"] {
        background: rgba(5, 9, 18, 0.88);
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .sidebar-brand {
        font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em;
        background: linear-gradient(90deg, #f8fafc, #a5b4fc);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-subtitle { color: #7c8aa5; font-size: 0.8rem; margin: 0.15rem 0 1.2rem 0; }
    .sidebar-section {
        color: #55657f; font-size: 0.68rem; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase; margin: 1.3rem 0 0.6rem 0;
    }
    .agent-chip {
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.45rem 0.75rem; margin-bottom: 0.3rem;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.055);
        border-radius: 9px; color: #b8c4d9; font-size: 0.82rem;
    }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: #6366f1;
           box-shadow: 0 0 8px rgba(99,102,241,0.8); flex-shrink: 0; }

    /* ---------- HERO ---------- */
    .hero { padding: 0.6rem 0 1.6rem 0; text-align: center; }
    .eyebrow {
        display: inline-flex; align-items: center; gap: 0.45rem;
        padding: 0.3rem 0.8rem; border-radius: 999px;
        background: rgba(99,102,241,0.10); border: 1px solid rgba(99,102,241,0.30);
        color: #a5b4fc; font-size: 0.7rem; font-weight: 600;
        letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 1.1rem;
    }
    .pulse-dot {
        width: 7px; height: 7px; border-radius: 50%; background: #34d399;
        box-shadow: 0 0 0 0 rgba(52,211,153,0.6); animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(52,211,153,0.55); }
        70%  { box-shadow: 0 0 0 8px rgba(52,211,153,0); }
        100% { box-shadow: 0 0 0 0 rgba(52,211,153,0); }
    }
    .hero-title {
        font-size: 3.1rem; line-height: 1.08; font-weight: 800;
        letter-spacing: -0.045em; color: #f8fafc; margin: 0;
    }
    .hero-title .grad {
        background: linear-gradient(92deg, #818cf8 0%, #38bdf8 55%, #a78bfa 100%);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-description {
        max-width: 620px; margin: 0.9rem auto 0 auto;
        color: #8fa0bc; font-size: 1rem; line-height: 1.7;
    }

    /* ---------- SECTION / CARD ---------- */
    .section-title { color: #f8fafc; font-size: 1.15rem; font-weight: 700;
                     letter-spacing: -0.01em; margin: 1.6rem 0 0.3rem 0; }
    .section-description { color: #64748b; font-size: 0.85rem; margin-bottom: 1rem; }
    .card {
        background: rgba(13, 20, 36, 0.66); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 1.15rem 1.25rem; backdrop-filter: blur(12px);
    }
    .metric-label { color: #64748b; font-size: 0.68rem; text-transform: uppercase;
                    letter-spacing: 0.10em; font-weight: 700; }

    /* ---------- DASHBOARD ---------- */
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.7rem; margin: 0 0 1rem 0; }
    .stat { padding: 0.8rem 1rem; border-radius: 12px;
            background: rgba(13,20,36,0.66); border: 1px solid rgba(255,255,255,0.07); }
    .stat-label { color: #64748b; font-size: 0.66rem; text-transform: uppercase;
                  letter-spacing: 0.10em; font-weight: 700; }
    .stat-value { color: #f8fafc; font-size: 1.4rem; font-weight: 750; margin-top: 0.15rem;
                  font-family: 'JetBrains Mono', monospace; }

    .flow-steps { display: flex; align-items: stretch; gap: 0.4rem; margin: 0 0 1rem 0; }
    .flow-step {
        flex: 1; min-width: 0; text-align: center; padding: 1rem 0.4rem; border-radius: 12px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.2s ease;
    }
    .flow-step.running { border-color: rgba(99,102,241,0.65); background: rgba(99,102,241,0.12);
                         box-shadow: 0 0 24px rgba(99,102,241,0.22); }
    .flow-step.done    { border-color: rgba(52,211,153,0.35); background: rgba(52,211,153,0.04); }
    .flow-step.error   { border-color: rgba(248,113,113,0.55); background: rgba(248,113,113,0.08); }
    .flow-icon { font-size: 1.35rem; }
    .flow-name { color: #cbd5e1; font-size: 0.78rem; margin-top: 0.4rem; font-weight: 600; }
    .flow-arrow { color: #3b4b68; font-size: 1rem; align-self: center; }
    .step-state { font-size: 0.68rem; margin-top: 0.3rem; font-weight: 600; }
    .step-state.pending { color: #475569; }
    .step-state.running { color: #818cf8; }
    .step-state.done    { color: #34d399; }
    .step-state.error   { color: #f87171; }
    .step-dur { color: #64748b; font-size: 0.66rem; margin-top: 0.15rem;
                font-family: 'JetBrains Mono', monospace; }
    .spin { display: inline-block; animation: rot 1.2s linear infinite; }
    @keyframes rot { to { transform: rotate(360deg); } }

    .now-box {
        margin: 0 0 1rem 0; padding: 0.65rem 0.95rem; border-radius: 10px;
        background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25);
        color: #c7d2fe; font-size: 0.82rem;
    }
    .rev-banner {
        margin: 0 0 1rem 0; padding: 0.6rem 0.95rem; border-radius: 10px;
        color: #fbbf24; background: rgba(251,191,36,0.08);
        border: 1px solid rgba(251,191,36,0.25); font-size: 0.8rem; font-weight: 600;
    }

    .bars { margin: 0 0 1rem 0; padding: 0.8rem 1rem; border-radius: 12px;
            background: rgba(13,20,36,0.66); border: 1px solid rgba(255,255,255,0.07); }
    .bar-row { display: flex; align-items: center; gap: 0.7rem; margin: 0.28rem 0; }
    .bar-label { width: 76px; color: #94a3b8; font-size: 0.74rem; flex-shrink: 0; }
    .bar-track { flex: 1; height: 8px; background: rgba(255,255,255,0.05);
                 border-radius: 99px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #6366f1, #38bdf8); }
    .bar-val { width: 56px; text-align: right; color: #64748b; font-size: 0.7rem;
               font-family: 'JetBrains Mono', monospace; }

    .flow-log { max-height: 280px; overflow-y: auto; background: rgba(8,12,22,0.6);
                border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.5rem; }
    .log-row { display: flex; gap: 0.7rem; padding: 0.42rem 0.6rem; border-radius: 8px; align-items: baseline; }
    .log-row:nth-child(odd) { background: rgba(255,255,255,0.02); }
    .log-row.rev  { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.18); }
    .log-row.warn { background: rgba(251,146,60,0.06); border: 1px solid rgba(251,146,60,0.2); }
    .log-row.err  { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.25); }
    .log-time { color: #475569; font-size: 0.68rem; font-family: 'JetBrains Mono', monospace; flex-shrink: 0; }
    .log-icon { flex-shrink: 0; }
    .log-msg { color: #b8c4d9; font-size: 0.8rem; line-height: 1.5; }

    /* ---------- SOURCES ---------- */
    .src-card { padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-radius: 11px;
                background: rgba(255,255,255,0.028); border: 1px solid rgba(255,255,255,0.055); }
    .src-card:hover { border-color: rgba(99,102,241,0.30); }
    .src-title { color: #e2e8f0; font-size: 0.9rem; font-weight: 650; }
    .src-url a { color: #818cf8; font-size: 0.75rem; text-decoration: none; word-break: break-all; }
    .src-url a:hover { text-decoration: underline; }

    /* ---------- ERROR ---------- */
    .err-card { padding: 1rem 1.2rem; border-radius: 14px; margin: 1rem 0;
                background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.35); }
    .err-title { color: #fca5a5; font-weight: 700; font-size: 1rem; }
    .err-msg { color: #fecaca; font-size: 0.85rem; margin-top: 0.4rem;
               font-family: 'JetBrains Mono', monospace; word-break: break-word; }
    .err-hint { color: #fbbf24; font-size: 0.82rem; margin-top: 0.6rem; }

    /* ---------- REPORT ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(13, 20, 36, 0.66); backdrop-filter: blur(12px); }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: rgba(255,255,255,0.07) !important; padding: 1.5rem 1.8rem;
    }
    [data-testid="stMarkdownContainer"] { color: #dbe4f0; line-height: 1.75; font-size: 0.95rem; }
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 { color: #f8fafc; }
    [data-testid="stMarkdownContainer"] code { background: rgba(99,102,241,0.12); color: #a5b4fc;
                                               padding: 0.15rem 0.4rem; border-radius: 5px; }

    /* ---------- EMPTY ---------- */
    .empty-state { text-align: center; padding: 3.5rem 1rem; border: 1px dashed rgba(255,255,255,0.10);
                   border-radius: 16px; background: rgba(255,255,255,0.015); margin-top: 1.5rem; }
    .empty-icon { width: 64px; height: 64px; margin: 0 auto 1.1rem auto; border-radius: 18px;
                  display: flex; align-items: center; justify-content: center; font-size: 1.8rem;
                  background: rgba(99,102,241,0.10); border: 1px solid rgba(99,102,241,0.25); }
    .empty-title { color: #e2e8f0; font-size: 1.1rem; font-weight: 700; }
    .empty-text { max-width: 460px; margin: 0.5rem auto 0 auto; color: #64748b;
                  line-height: 1.65; font-size: 0.87rem; }

    /* ---------- INPUTS / BUTTONS ---------- */
    textarea { background: rgba(10, 16, 30, 0.85) !important; color: #e2e8f0 !important;
               border: 1px solid rgba(255,255,255,0.09) !important; border-radius: 12px !important; }
    textarea:focus { border-color: rgba(99,102,241,0.55) !important;
                     box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important; }
    div.stButton > button {
        width: 100%; border-radius: 10px; border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.04); color: #cbd5e1; font-weight: 550;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover { border-color: rgba(129,140,248,0.5); background: rgba(99,102,241,0.10); color: #e0e7ff; }
    div.stButton > button[kind="primary"] {
        border: 1px solid rgba(129,140,248,0.40);
        background: linear-gradient(135deg, #6366f1, #4f46e5); color: white;
        font-weight: 650; min-height: 2.75rem; box-shadow: 0 4px 20px rgba(99,102,241,0.35);
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4f46e5, #4338ca); border-color: #818cf8;
        box-shadow: 0 6px 28px rgba(99,102,241,0.50); transform: translateY(-1px); color: white;
    }
    div.stDownloadButton > button {
        border-radius: 10px; border: 1px solid rgba(129,140,248,0.35);
        background: rgba(99,102,241,0.12); color: #a5b4fc; font-weight: 600;
    }
    div.stDownloadButton > button:hover { background: rgba(99,102,241,0.22); border-color: #818cf8; color: #e0e7ff; }

    hr { border-color: rgba(255,255,255,0.06) !important; }
    .footer { text-align: center; color: #3d4c68; font-size: 0.73rem; margin-top: 3rem;
              font-family: 'JetBrains Mono', monospace; letter-spacing: 0.04em; }

    @media (max-width: 760px) {
        .stat-row { grid-template-columns: repeat(2, 1fr); }
        .hero-title { font-size: 2.2rem; }
        .flow-steps { flex-wrap: wrap; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_html(block: str) -> str:
    """Dedent and collapse blank lines so Streamlit keeps the HTML as ONE block."""
    return re.sub(r"\n\s*\n+", "\n", textwrap.dedent(block)).strip()


def ui(block: str) -> None:
    st.markdown(clean_html(block), unsafe_allow_html=True)


def to_text(content) -> str:
    """Flatten LangChain content blocks / lists / messages into plain markdown text."""
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


def fmt_secs(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs:02d}s"


def safe_url(url: str) -> str:
    return url if str(url).startswith(("http://", "https://")) else "#"


def friendly_hint(error_text: str) -> str:
    text = error_text.lower()
    if any(k in text for k in ("api_key", "api key", "401", "unauthorized", "authentication", "permission")):
        return "API key problem — check your .env (GOOGLE_API_KEY and TAVILY_API_KEY)."
    if any(k in text for k in ("429", "rate limit", "rate_limit", "quota", "resource_exhausted")):
        return "Rate limit or quota hit — wait a minute and retry."
    if any(k in text for k in ("timeout", "timed out", "connection", "dns", "network")):
        return "Network problem or timeout — check your connection and retry."
    if any(k in text for k in ("context length", "maximum context", "too many tokens", "413")):
        return "The prompt got too long for the model — the Reader pulled too much page text."
    if "no results" in text:
        return "Tavily returned nothing — try rephrasing the question."
    if "none of the sources" in text:
        return "Every source failed to load — some sites block scrapers. Retry or rephrase."
    if "no module named" in text or "modulenotfound" in text:
        return "A Python package is missing — pip install it in the active environment."
    return "Open the traceback below to see which agent and line failed."


# ============================================================
# FLOW MODEL + RENDERING
# ============================================================

STEP_ORDER = ("search", "read", "write", "critic")
STEP_META = {
    "search": ("🔎", "Search"),
    "read": ("📖", "Read"),
    "write": ("✍️", "Write"),
    "critic": ("🧐", "Critic"),
}
STATE_BADGE = {
    "pending": "○ queued",
    "running": '<span class="spin">⏳</span> working',
    "done": "✓ done",
    "error": "✕ failed",
}
EVENT_TEXT = {
    "search_start": ("🔎", "Search Agent started — querying the web…"),
    "search_fallback": ("🛟", "Agent skipped the search tool — calling it directly"),
    "search_done": ("✅", "Search finished — {n} source(s) found"),
    "read_start": ("📖", "Reader Agent started — analyzing sources…"),
    "read_progress": ("📄", "Reading {i}/{total}: {title}"),
    "source_failed": ("⚠️", "Skipped “{title}” — {reason}"),
    "read_done": ("✅", "Reader finished — {n} source(s) summarized"),
    "write_start": ("✍️", "Writer Agent drafting report (round {round})…"),
    "write_done": ("✅", "Writer finished draft (round {round})"),
    "critic_start": ("🧐", "Critic Agent reviewing the draft…"),
    "critic_done": ("✅", "Critic approved the report"),
    "critic_revision": ("🔁", "Critic requested a revision → round {round}: “{feedback}”"),
    "retry": ("🔄", "Temporary API error in {step} step — retry {attempt}/{max} in {wait}s"),
    "error": ("❌", "Pipeline failed: {message}"),
}
ROW_CLASS = {
    "critic_revision": " rev",
    "source_failed": " warn",
    "search_fallback": " warn",
    "retry": " warn",
    "error": " err",
}


def format_event(event: dict):
    event_type = event["type"]
    icon, template = EVENT_TEXT.get(event_type, ("•", "{type}"))

    if event_type == "critic_done" and event.get("approved") is False:
        icon, template = "⚠️", "Revision limit reached — returning the latest draft"

    values = {"type": event_type}
    for key, value in event.items():
        if key in ("type", "time", "ts", "sources"):
            continue
        text = str(value)
        if len(text) > 160:
            text = text[:160] + "…"
        values[key] = html.escape(text)

    try:
        message = template.format(**values)
    except Exception:
        message = html.escape(template)
    return icon, message


def analyse(events: list, failed: bool = False):
    """Derive step states, durations, counters and read progress from the event list."""
    states = {key: "pending" for key in STEP_ORDER}
    durations = {key: 0.0 for key in STEP_ORDER}
    starts: dict = {}
    revisions = 0
    sources = findings = "–"
    read_progress = None

    for event in events:
        event_type, stamp = event.get("type", ""), event.get("ts")
        step = event_type.rsplit("_", 1)[0]

        if event_type.endswith("_start") and step in states:
            states[step] = "running"
            if stamp:
                starts[step] = stamp
        elif event_type.endswith("_done") and step in states:
            states[step] = "done"
            if stamp and step in starts:
                durations[step] += stamp - starts.pop(step)
            if step == "search":
                sources = event.get("n", "–")
            elif step == "read":
                findings = event.get("n", "–")
                read_progress = None
        elif event_type == "read_progress":
            read_progress = (event.get("i", 0), event.get("total", 0))
        elif event_type == "critic_revision":
            revisions += 1
            if stamp and "critic" in starts:
                durations["critic"] += stamp - starts.pop("critic")
            states["write"] = "pending"
            states["critic"] = "pending"

    if failed:
        for key, value in states.items():
            if value == "running":
                states[key] = "error"

    return states, durations, revisions, sources, findings, read_progress


def progress_value(events: list) -> float:
    states, _, _, _, _, read_progress = analyse(events)
    done = sum(1 for state in states.values() if state == "done")
    partial = 0.0
    if read_progress and read_progress[1] and states["read"] == "running":
        partial = read_progress[0] / read_progress[1]
    return min((done + partial) / len(STEP_ORDER), 0.95)


def render_dashboard(
    events: list,
    elapsed: float = 0.0,
    failed: bool = False,
    running: bool = False,
) -> str:
    states, durations, revisions, sources, findings, read_progress = analyse(events, failed)
    parts = []

    # stat cards
    parts.append(
        '<div class="stat-row">'
        f'<div class="stat"><div class="stat-label">Elapsed</div><div class="stat-value">{fmt_secs(elapsed)}</div></div>'
        f'<div class="stat"><div class="stat-label">Sources</div><div class="stat-value">{html.escape(str(sources))}</div></div>'
        f'<div class="stat"><div class="stat-label">Summarized</div><div class="stat-value">{html.escape(str(findings))}</div></div>'
        f'<div class="stat"><div class="stat-label">Revisions</div><div class="stat-value">{revisions}</div></div>'
        '</div>'
    )

    # pipeline steps
    parts.append('<div class="flow-steps">')
    for key in STEP_ORDER:
        icon, name = STEP_META[key]
        state = states[key]

        extra = ""
        if state == "running" and key == "read" and read_progress:
            extra = f'<div class="step-dur">{read_progress[0]}/{read_progress[1]}</div>'
        elif durations[key]:
            extra = f'<div class="step-dur">{fmt_secs(durations[key])}</div>'

        parts.append(
            f'<div class="flow-step {state}">'
            f'<div class="flow-icon">{icon}</div>'
            f'<div class="flow-name">{name}</div>'
            f'<div class="step-state {state}">{STATE_BADGE[state]}</div>'
            f'{extra}'
            '</div>'
        )
        if key != STEP_ORDER[-1]:
            parts.append('<div class="flow-arrow">→</div>')
    parts.append('</div>')

    # "right now" line, only while the pipeline is running
    if running and events:
        icon, message = format_event(events[-1])
        parts.append(f'<div class="now-box">{icon} {message}</div>')

    if revisions:
        plural = "s" if revisions > 1 else ""
        parts.append(
            f'<div class="rev-banner">🔁 Critic sent {revisions} revision request{plural} — report was re-drafted</div>'
        )

    # time-share bars
    total = sum(durations.values())
    if total > 0:
        parts.append('<div class="bars">')
        for key in STEP_ORDER:
            icon, name = STEP_META[key]
            percent = durations[key] / total * 100
            parts.append(
                '<div class="bar-row">'
                f'<div class="bar-label">{icon} {name}</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{percent:.1f}%"></div></div>'
                f'<div class="bar-val">{fmt_secs(durations[key])}</div>'
                '</div>'
            )
        parts.append('</div>')

    # event log
    if events:
        rows = []
        for event in events:
            icon, message = format_event(event)
            css = ROW_CLASS.get(event.get("type"), "")
            rows.append(
                f'<div class="log-row{css}">'
                f'<span class="log-time">{event.get("time", "")}</span>'
                f'<span class="log-icon">{icon}</span>'
                f'<span class="log-msg">{message}</span>'
                '</div>'
            )
        parts.append('<div class="flow-log">' + "".join(rows) + '</div>')

    return "".join(parts)  # one line, no blank lines → safe for st.markdown


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "question_input": "",
    "question": "",
    "result": None,        # {"report", "sources", "findings"}
    "events": [],
    "elapsed": 0.0,
    "error": None,
    "traceback": None,
    "history": [],         # past successful runs
}
for state_key, state_default in DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = state_default


def set_example(text: str) -> None:
    st.session_state.question_input = text


def clear_results() -> None:
    st.session_state.result = None
    st.session_state.events = []
    st.session_state.error = None
    st.session_state.traceback = None
    st.session_state.elapsed = 0.0


def load_history(index: int) -> None:
    run = st.session_state.history[index]
    st.session_state.question = run["question"]
    st.session_state.question_input = run["question"]
    st.session_state.result = run["result"]
    st.session_state.events = run["events"]
    st.session_state.elapsed = run["elapsed"]
    st.session_state.error = None
    st.session_state.traceback = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    ui(
        """
        <div class="sidebar-brand">🔬 Researcher</div>
        <div class="sidebar-subtitle">Multi-Agent AI Research System</div>
        """
    )

    ui('<div class="sidebar-section">Settings</div>')
    max_revisions = st.slider(
        "Max critic rounds",
        min_value=1,
        max_value=5,
        value=DEFAULT_MAX_REVISIONS,
        help="How many times the Critic can review the report. More rounds cost more time and tokens.",
    )

    strict_critic = st.toggle(
        "Strict critic",
        value=False,
        help="Critic only approves if every claim cites its source, a Sources list and "
             "a Limitations section exist. Use it to see the rejection and revision loop.",
    )

    ui('<div class="sidebar-section">Agents</div>')
    ui(
        """
        <div class="agent-chip"><span class="dot"></span>Search — finds sources (Tavily)</div>
        <div class="agent-chip"><span class="dot"></span>Reader — extracts findings</div>
        <div class="agent-chip"><span class="dot"></span>Writer — drafts the report</div>
        <div class="agent-chip"><span class="dot"></span>Critic — reviews, requests fixes</div>
        """
    )

    if st.session_state.history:
        ui('<div class="sidebar-section">History</div>')
        for index in range(len(st.session_state.history) - 1, -1, -1):
            run = st.session_state.history[index]
            label = run["question"][:38] + ("…" if len(run["question"]) > 38 else "")
            st.button(
                f"🕘 {label}",
                key=f"history_{index}",
                on_click=load_history,
                args=(index,),
            )

    if st.session_state.result or st.session_state.error:
        st.markdown("")
        st.button("🗑️ Clear results", on_click=clear_results)


# ============================================================
# HERO
# ============================================================

ui(
    """
    <div class="hero">
        <div class="eyebrow"><span class="pulse-dot"></span> Multi-Agent Research</div>
        <h1 class="hero-title">Research with <span class="grad">AI agents.</span></h1>
        <p class="hero-description">
            Ask a question. Search, Reader, Writer and Critic agents investigate
            the web, write a report, and review it before you see it.
        </p>
    </div>
    """
)


# ============================================================
# INPUT
# ============================================================

question = st.text_area(
    "Research question",
    key="question_input",
    placeholder="Example: What are the benefits of using CAG for LLMs?",
    height=110,
    label_visibility="collapsed",
)

EXAMPLES = (
    "What are the benefits of using CAG for LLMs?",
    "How is agentic AI used in healthcare?",
    "RAG vs fine-tuning: when to use which?",
)
example_cols = st.columns(len(EXAMPLES))
for column, example in zip(example_cols, EXAMPLES):
    with column:
        st.button(
            f"💡 {example}",
            key=f"example_{example}",
            on_click=set_example,
            args=(example,),
        )

st.markdown("")
run_button = st.button("🚀 Start Research", type="primary")


# ============================================================
# EXECUTION  (worker thread + live dashboard on the main thread)
# ============================================================

if run_button:
    if not question.strip():
        st.warning("Please enter a research question.")
    else:
        clear_results()
        st.session_state.question = question.strip()

        st.markdown("---")
        ui('<div class="section-title">Research in progress</div>')
        ui('<div class="section-description">Live view of the agent pipeline, including every critic revision.</div>')

        progress = st.progress(0.0)
        dashboard = st.empty()

        # plain values captured by the worker (threads must not touch st.session_state)
        research_question = st.session_state.question
        rounds = int(max_revisions)
        strict = bool(strict_critic)

        events: list = []
        event_queue: "queue.Queue[dict]" = queue.Queue()
        outcome: dict = {}

        def on_event(event: dict) -> None:
            # Worker thread: only enqueue. Never call Streamlit from here.
            item = dict(event)
            item["ts"] = time.time()
            item["time"] = time.strftime("%H:%M:%S")
            event_queue.put(item)

        def worker() -> None:
            try:
                raw = run_research(
                    research_question,
                    on_event=on_event,
                    max_revisions=rounds,
                    strict_critic=strict,
                )

                if isinstance(raw, dict):
                    report = to_text(raw.get("report")).strip()
                    sources = raw.get("sources", [])
                    findings = raw.get("findings", [])
                else:  # old-style return: just the report
                    report, sources, findings = to_text(raw).strip(), [], []

                if not report:
                    raise ValueError("The research workflow returned an empty report.")

                outcome["result"] = {
                    "report": report,
                    "sources": sources,
                    "findings": findings,
                }
            except Exception as exc:  # noqa: BLE001 — everything goes to the UI
                outcome["error"] = f"{type(exc).__name__}: {exc}"
                outcome["traceback"] = traceback.format_exc()
                on_event({"type": "error", "message": outcome["error"]})

        thread = threading.Thread(target=worker, daemon=True)
        started = time.time()
        thread.start()

        last_draw = 0.0
        while thread.is_alive() or not event_queue.empty():
            got_event = False
            try:
                events.append(event_queue.get(timeout=0.2))
                got_event = True
            except queue.Empty:
                pass

            now = time.time()
            if got_event or now - last_draw > 0.4:
                progress.progress(progress_value(events))
                dashboard.markdown(
                    render_dashboard(events, elapsed=now - started, running=True),
                    unsafe_allow_html=True,
                )
                last_draw = now

        thread.join()
        elapsed = time.time() - started

        st.session_state.events = events
        st.session_state.elapsed = elapsed

        if "error" in outcome:
            st.session_state.error = outcome["error"]
            st.session_state.traceback = outcome.get("traceback")
        else:
            st.session_state.result = outcome["result"]
            st.session_state.history.append(
                {
                    "question": st.session_state.question,
                    "result": outcome["result"],
                    "events": events,
                    "elapsed": elapsed,
                }
            )

        st.rerun()  # redraw cleanly from session state


# ============================================================
# RESULTS / ERROR
# ============================================================

result = st.session_state.result
has_error = bool(st.session_state.error)

if result or has_error:
    st.markdown("---")
    ui('<div class="section-title">Research results</div>')

    ui(
        f"""
        <div class="card">
            <div class="metric-label">Question</div>
            <div style="color:#e2e8f0;font-size:1rem;margin-top:0.4rem;line-height:1.55;">
                {html.escape(st.session_state.question)}
            </div>
        </div>
        """
    )
    st.markdown("")

    if has_error:
        error_text = st.session_state.error
        ui(
            f"""
            <div class="err-card">
                <div class="err-title">❌ The research workflow failed</div>
                <div class="err-msg">{html.escape(error_text)}</div>
                <div class="err-hint">💡 {html.escape(friendly_hint(error_text))}</div>
            </div>
            """
        )
        if st.session_state.traceback:
            with st.expander("Show full traceback"):
                st.code(st.session_state.traceback, language="python")

    tab_names = ["📄 Report", "🔗 Sources", "⚙️ Agent Process"] if result else ["⚙️ Agent Process"]
    tabs = st.tabs(tab_names)

    if result:
        report_text = to_text(result["report"])
        sources = result.get("sources", [])
        findings = result.get("findings", [])

        # ---------- REPORT ----------
        with tabs[0]:
            with st.container(border=True):
                # unsafe_allow_html=False → agent output can never inject HTML/JS
                st.markdown(report_text, unsafe_allow_html=False)

            full_markdown = report_text
            if sources:
                source_lines = "\n".join(f"- [{s['title']}]({s['url']})" for s in sources)
                full_markdown += f"\n\n## Sources\n\n{source_lines}\n"

            col_a, col_b, _ = st.columns([1, 1, 3])
            with col_a:
                st.download_button(
                    "⬇️ Download .md",
                    data=full_markdown.encode("utf-8"),
                    file_name="research_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_b:
                st.download_button(
                    "⬇️ Download .txt",
                    data=full_markdown.encode("utf-8"),
                    file_name="research_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        # ---------- SOURCES ----------
        with tabs[1]:
            if not sources:
                st.info("No source information was returned for this run.")

            findings_by_url = {item.get("url"): item.get("findings", "") for item in findings}

            for number, source in enumerate(sources, start=1):
                url = safe_url(source["url"])
                ui(
                    f"""
                    <div class="src-card">
                        <div class="src-title">{number}. {html.escape(source["title"])}</div>
                        <div class="src-url"><a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(source["url"])}</a></div>
                    </div>
                    """
                )
                source_findings = findings_by_url.get(source["url"])
                if source_findings:
                    with st.expander("What the Reader extracted"):
                        st.markdown(to_text(source_findings), unsafe_allow_html=False)
                else:
                    st.caption("⚠️ This source could not be read and was skipped.")

        process_tab = tabs[2]
    else:
        process_tab = tabs[0]

    # ---------- AGENT PROCESS ----------
    with process_tab:
        if st.session_state.events:
            st.markdown(
                render_dashboard(
                    st.session_state.events,
                    elapsed=st.session_state.elapsed,
                    failed=has_error,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info("No agent events were recorded for this run.")

elif not run_button:
    st.markdown("---")
    ui(
        """
        <div class="empty-state">
            <div class="empty-icon">🔬</div>
            <div class="empty-title">Ready to research</div>
            <div class="empty-text">
                Type a question or pick an example above. The agents will search,
                read, write and critique the result for you.
            </div>
        </div>
        """
    )

ui('<div class="footer">Built with Python · LangChain · Gemini · Tavily · Streamlit</div>')