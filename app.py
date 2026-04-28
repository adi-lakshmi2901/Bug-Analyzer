"""FastHTML web UI for Bug Analysis Agent."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from fasthtml.common import *

from bug_analysis_agent import BugAnalysisAgent
from models import Issue
from config import LoggingConfig

# Load .env and alias GEMINI_API_KEY -> GOOGLE_API_KEY if needed
load_dotenv()
if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

LoggingConfig.setup_logging("WARNING")

BUGS_FILE = "bugs.md"
MODEL = "google-gla:gemini-2.5-flash"

_agent = None


def get_agent() -> BugAnalysisAgent:
    global _agent
    if _agent is None:
        _agent = BugAnalysisAgent(requirements_folder=".", model_name=MODEL)
    return _agent


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

CSS = Style("""
:root {
    --bg: #f7f7f8;
    --surface: #ffffff;
    --border: #e4e4e7;
    --text: #18181b;
    --muted: #71717a;
    --accent: #6366f1;
    --accent-light: #eef2ff;
    --green: #22c55e;
    --yellow: #f59e0b;
    --red: #ef4444;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}

.container {
    max-width: 740px;
    margin: 0 auto;
    padding: 52px 24px 80px;
}

/* Header */
.header { margin-bottom: 36px; }
.header h1 {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.header p {
    color: var(--muted);
    margin-top: 6px;
    font-size: 0.875rem;
    line-height: 1.5;
}

/* Input grid */
.inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 20px;
}
@media (max-width: 560px) { .inputs { grid-template-columns: 1fr; } }

/* Card */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
}
.card-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-bottom: 12px;
}

/* Inputs */
textarea, input[type=number] {
    width: 100%;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 9px 12px;
    font-size: 0.875rem;
    font-family: inherit;
    color: var(--text);
    background: var(--bg);
    resize: vertical;
    transition: border-color .15s, box-shadow .15s;
}
textarea { min-height: 100px; }
textarea:focus, input[type=number]:focus {
    outline: none;
    border-color: var(--accent);
    background: #fff;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}

/* Button */
.btn {
    margin-top: 12px;
    width: 100%;
    background: var(--accent);
    color: #fff;
    border: none;
    padding: 9px 16px;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background .15s, opacity .15s;
}
.btn:hover { background: #4f46e5; }
form.htmx-request .btn {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Loading indicator */
.loading-msg {
    margin-top: 9px;
    font-size: 0.8rem;
    color: var(--muted);
    text-align: center;
    opacity: 0;
    transition: opacity 200ms ease-in;
}
.htmx-request .loading-msg { opacity: 1; }

/* Result area */
#result { margin-top: 6px; }

/* Result card */
.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
}
.result-issue {
    font-size: 0.85rem;
    color: var(--muted);
    background: var(--bg);
    border-left: 3px solid #d1d5db;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 22px;
    line-height: 1.55;
    word-break: break-word;
}
.meta-row { margin-bottom: 18px; }
.meta-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--muted);
    margin-bottom: 7px;
}
.category-badge {
    display: inline-block;
    background: var(--accent-light);
    color: var(--accent);
    border: 1px solid #c7d2fe;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    font-weight: 600;
}
.confidence-bar-bg {
    background: #ebebeb;
    border-radius: 4px;
    height: 6px;
    margin: 7px 0 5px;
}
.confidence-bar-fill { height: 6px; border-radius: 4px; }
.confidence-value { font-size: 0.82rem; font-weight: 600; }
.reasoning-text {
    font-size: 0.875rem;
    line-height: 1.72;
    color: #333;
}

/* Error */
.error-card {
    background: #fff5f5;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 16px 20px;
    color: var(--red);
    font-size: 0.875rem;
    line-height: 1.5;
}
""")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app, rt = fast_app(pico=False, hdrs=(CSS,))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def confidence_color(c: int) -> str:
    if c >= 80:
        return "var(--green)"
    if c >= 50:
        return "var(--yellow)"
    return "var(--red)"


def result_view(result, issue_label: str):
    color = confidence_color(result.confidence)
    return Div(
        Div(issue_label, cls="result-issue"),
        Div(
            P("Category", cls="meta-label"),
            Span(result.category.value, cls="category-badge"),
            cls="meta-row"
        ),
        Div(
            P("Confidence", cls="meta-label"),
            Div(
                Div(
                    style=f"width:{result.confidence}%;background:{color}",
                    cls="confidence-bar-fill"
                ),
                cls="confidence-bar-bg"
            ),
            P(f"{result.confidence}%", cls="confidence-value", style=f"color:{color}"),
            cls="meta-row"
        ),
        Div(
            P("Reasoning", cls="meta-label"),
            P(result.reasoning, cls="reasoning-text"),
            cls="meta-row"
        ),
        cls="result-card"
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@rt("/")
def get():
    return (
        Title("Bug Analysis Agent"),
        Main(
            Div(
                H1("Bug Analysis Agent"),
                P("Analyze a bug by free-form description, or by its ID number in bugs.md."),
                cls="header"
            ),
            Div(
                Div(
                    P("By Description", cls="card-title"),
                    Form(
                        Textarea(
                            name="description",
                            placeholder="Describe the bug or requirement issue...",
                        ),
                        Button("Analyze", type="submit", cls="btn"),
                        P("Analyzing...", cls="loading-msg"),
                        hx_post="/analyze/description",
                        hx_target="#result",
                        hx_swap="innerHTML",
                    ),
                    cls="card"
                ),
                Div(
                    P("By Bug ID", cls="card-title"),
                    Form(
                        Input(
                            type="number",
                            name="bug_id",
                            min="1",
                            step="1",
                            placeholder="e.g. 3",
                        ),
                        Button("Analyze", type="submit", cls="btn"),
                        P("Analyzing...", cls="loading-msg"),
                        hx_post="/analyze/bug",
                        hx_target="#result",
                        hx_swap="innerHTML",
                    ),
                    cls="card"
                ),
                cls="inputs"
            ),
            Div(id="result"),
            cls="container"
        )
    )


@rt("/analyze/description")
async def post(description: str = ""):
    description = description.strip()
    if not description:
        return Div("Please enter a bug description.", cls="error-card")

    issue = Issue(number=1, text=description, has_existing_analysis=False)
    a = get_agent()

    try:
        requirements = await asyncio.to_thread(a._load_requirements)
        result = await asyncio.to_thread(
            a.analysis_engine.analyze_issue, issue, requirements
        )
        if not result:
            return Div("Analysis failed. Please try again.", cls="error-card")
        return result_view(result, f'"{description}"')
    except Exception as e:
        return Div(f"Error: {str(e)}", cls="error-card")


@rt("/analyze/bug")
async def post(bug_id: str = ""):
    bid = bug_id.strip()
    if not bid or not bid.isdigit() or int(bid) < 1:
        return Div("Please enter a valid bug number.", cls="error-card")

    bug_num = int(bid)
    a = get_agent()
    bugs_path = Path(BUGS_FILE)

    if not bugs_path.exists():
        return Div("bugs.md not found in current directory.", cls="error-card")

    try:
        bug_report = await asyncio.to_thread(
            a.file_processor.parse_bugs_file, str(bugs_path)
        )
        target = next((i for i in bug_report.issues if i.number == bug_num), None)

        if not target:
            return Div(f"Bug #{bug_num} not found in bugs.md.", cls="error-card")

        requirements = await asyncio.to_thread(a._load_requirements)
        result = await asyncio.to_thread(
            a.analysis_engine.analyze_issue, target, requirements
        )

        if not result:
            return Div("Analysis failed. Please try again.", cls="error-card")

        return result_view(result, f"#{bug_num}: {target.text}")
    except Exception as e:
        return Div(f"Error: {str(e)}", cls="error-card")


serve()
