"""Generate print-friendly SVG diagrams used by the AIML-451 dissertation.

The diagrams are deliberately generated from small declarative layouts rather
than copied from a generic architecture template.  Their labels mirror the
current InsightForge modules, routes, models, and execution paths.
"""
from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "report_assets" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
NAVY = "#17324d"
BLUE = "#2563eb"
TEAL = "#0f766e"
SLATE = "#f1f5f9"
PALE = "#e8f1f8"
INK = "#1e293b"
MUTED = "#475569"
LINE = "#64748b"
ORANGE = "#b45309"


def svg_start(title: str, subtitle: str = "") -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="55" y="48" font-family="Arial" font-size="27" font-weight="700" fill="{NAVY}">{escape(title)}</text>',
    ] + ([f'<text x="55" y="76" font-family="Arial" font-size="16" fill="{MUTED}">{escape(subtitle)}</text>'] if subtitle else [])


def box(parts: list[str], x: int, y: int, w: int, h: int, title: str, lines: list[str], fill: str = PALE, stroke: str = NAVY) -> None:
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
    parts.append(f'<text x="{x + 18}" y="{y + 34}" font-family="Arial" font-size="21" font-weight="700" fill="{NAVY}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x + 18}" y="{y + 68 + i * 25}" font-family="Arial" font-size="17" fill="{INK}">{escape(line)}</text>')


def arrow(parts: list[str], x1: int, y1: int, x2: int, y2: int, label: str | None = None, dashed: bool = False) -> None:
    dash = ' stroke-dasharray="9 7"' if dashed else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="3" marker-end="url(#arrow)"{dash}/>')
    if label:
        parts.append(f'<text x="{(x1+x2)//2}" y="{(y1+y2)//2-8}" text-anchor="middle" font-family="Arial" font-size="15" fill="{MUTED}">{escape(label)}</text>')


def finish(parts: list[str], name: str) -> None:
    parts.append("</svg>")
    (OUT / f"{name}.svg").write_text("\n".join(parts), encoding="utf-8")


def architecture() -> None:
    p = svg_start("High-level InsightForge architecture", "Verified modular-monolith boundary; optional services are shown with dashed connectors.")
    box(p, 45, 260, 250, 210, "Browser client", ["Next.js App Router", "Dashboard / datasets", "Explore / Analyse / Insights"], SLATE)
    box(p, 360, 210, 290, 300, "FastAPI gateway", ["JWT dependency", "Owner lookup", "Rate limits", "REST response contracts"], PALE)
    box(p, 735, 105, 300, 220, "Background jobs", ["JobManager", "ThreadPoolExecutor", "Upload / auto-analysis", "Polling endpoint"], "#fff7ed", ORANGE)
    box(p, 735, 390, 300, 220, "Agent and analytics", ["PlannerAgent", "LangGraph workflow", "Semantic understanding", "AutoAnalysisEngine"], "#ecfdf5", TEAL)
    box(p, 1115, 175, 390, 250, "Execution tools", ["DuckDB SELECT-only SQL", "AST-allowlisted Pandas", "Charts / profiler", "Isolation Forest"], "#eff6ff", BLUE)
    box(p, 1115, 535, 390, 205, "Persistence", ["SQLite / PostgreSQL", "DatasetRegistry + CSV files", "Chat sessions / messages", "Cached reports"], SLATE)
    box(p, 735, 710, 300, 105, "Optional integrations", ["Gemini · Upstash Redis · Vector"], "#fefce8", ORANGE)
    arrow(p, 295, 365, 360, 365, "HTTPS / JSON")
    arrow(p, 650, 285, 735, 215, "heavy work")
    arrow(p, 650, 410, 735, 490, "chat")
    arrow(p, 1035, 215, 1115, 285)
    arrow(p, 1035, 500, 1115, 330)
    arrow(p, 1035, 560, 1115, 635)
    arrow(p, 650, 460, 1115, 635, "metadata / files")
    arrow(p, 885, 710, 885, 610, "when configured", True)
    finish(p, "architecture")


def context_dfd() -> None:
    p = svg_start("Context-level data-flow diagram", "The browser communicates only through authenticated API contracts.")
    box(p, 65, 320, 245, 155, "User / analyst", ["Upload CSV", "Ask questions", "Review evidence"], SLATE)
    box(p, 425, 250, 350, 260, "InsightForge API", ["Auth + owner checks", "Upload / chat / tools", "Jobs + insight routes"], PALE)
    box(p, 945, 130, 260, 155, "Dataset store", ["Registry", "CSV file", "Schema metadata"], "#eff6ff", BLUE)
    box(p, 945, 365, 260, 155, "Analysis services", ["Profile", "Semantic model", "Charts / anomaly"], "#ecfdf5", TEAL)
    box(p, 945, 600, 260, 155, "Memory + reports", ["Sessions / messages", "Auto-analysis JSON"], SLATE)
    box(p, 1300, 330, 235, 190, "Optional adapters", ["Gemini", "Upstash Redis", "Upstash Vector"], "#fefce8", ORANGE)
    arrow(p, 310, 395, 425, 395, "HTTPS / bearer token")
    arrow(p, 775, 315, 945, 205, "validated data")
    arrow(p, 775, 390, 945, 440, "typed request")
    arrow(p, 775, 455, 945, 680, "history / report")
    arrow(p, 1205, 440, 1300, 425, "optional", True)
    finish(p, "context_dfd")


def upload_flow() -> None:
    p = svg_start("Level-1 upload and automatic-analysis flow", "A valid upload is registered before the report job completes.")
    box(p, 45, 320, 215, 145, "UploadPanel", ["File selection", "POST /api/upload"], SLATE)
    box(p, 345, 255, 255, 275, "CsvIngestionService", ["Extension / size", "Decode / parse", "Headers / row limit", "Conservative dates"], PALE)
    box(p, 685, 320, 230, 145, "DatasetRegistry", ["Owner-scoped ID", "Cache + CSV file"], "#eff6ff", BLUE)
    box(p, 1000, 120, 255, 145, "Metadata DB", ["DatasetModel", "Schema + row count"], SLATE)
    box(p, 1000, 320, 255, 145, "JobManager", ["auto_analysis", "processing / polling"], "#fff7ed", ORANGE)
    box(p, 1000, 520, 255, 145, "StatisticalPass", ["Semantic model", "Quality / metrics", "Charts"], "#ecfdf5", TEAL)
    box(p, 1320, 520, 220, 145, "DeterministicFallback", ["Cards", "Recommendations", "Report JSON"], "#ecfdf5", TEAL)
    arrow(p, 260, 392, 345, 392, "bytes")
    arrow(p, 600, 392, 685, 392, "DataFrame")
    arrow(p, 800, 320, 1000, 190, "metadata")
    arrow(p, 800, 425, 1000, 392, "submit")
    arrow(p, 1125, 465, 1125, 520, "worker")
    arrow(p, 1255, 592, 1320, 592)
    finish(p, "upload_flow")


def structure_chart() -> None:
    p = svg_start("Structure chart and work-breakdown structure", "Repository modules are grouped by responsibility, not deployed as separate microservices.")
    box(p, 640, 95, 320, 105, "InsightForge", ["end-to-end application"], PALE)
    branches = [
        (65, 300, "Frontend", ["App Router pages", "Components / state", "API client"]),
        (360, 300, "API + identity", ["FastAPI routes", "JWT / rate limits", "Pydantic contracts"]),
        (655, 300, "Data + persistence", ["Ingestion", "Registry / DB", "Memory layers"]),
        (950, 300, "Analytics", ["Understanding", "Auto analysis", "Profiler / charts"]),
        (1245, 300, "Safe tools", ["DuckDB", "Pandas AST", "Anomalies"]),
    ]
    for x, y, t, ls in branches:
        box(p, x, y, 245, 180, t, ls, SLATE if t != "Analytics" else "#ecfdf5", TEAL if t == "Analytics" else NAVY)
        arrow(p, 800, 200, x + 122, y)
    box(p, 360, 620, 880, 120, "Verification stream", ["Pytest unit/regression tests · HTTP route tests · persistence isolation · Next.js production build"], "#fefce8", ORANGE)
    arrow(p, 800, 480, 800, 620, "cross-cutting evidence")
    finish(p, "structure_chart")


def agent_flow() -> None:
    p = svg_start("Agent and tool-execution flow", "LangGraph is used for generic requests; deterministic business-question handling runs before the generic fallback.")
    box(p, 55, 345, 210, 125, "User message", ["natural-language question"], SLATE)
    box(p, 345, 300, 220, 180, "classify_intent", ["visualization", "anomaly", "profile", "query"] , PALE)
    box(p, 645, 300, 230, 180, "select_tool", ["Gemini JSON plan", "or rule-based fallback"], "#fefce8", ORANGE)
    box(p, 955, 300, 230, 180, "execute_tool", ["SQL / Pandas", "chart / profile", "anomaly"], "#eff6ff", BLUE)
    box(p, 1265, 300, 250, 180, "validate_result", ["success?", "retry < 2?"], "#ecfdf5", TEAL)
    box(p, 1020, 625, 225, 125, "synthesize_answer", ["AnalysisResponse", "evidence + chart"], PALE)
    box(p, 1320, 625, 225, 125, "fallback_deterministic", ["PlannerAgent", "safe baseline"], "#fff7ed", ORANGE)
    arrow(p, 265, 407, 345, 390)
    arrow(p, 565, 390, 645, 390)
    arrow(p, 875, 390, 955, 390)
    arrow(p, 1185, 390, 1265, 390)
    arrow(p, 1390, 480, 1130, 625, "success")
    arrow(p, 1510, 480, 1430, 625, "retries exhausted")
    arrow(p, 1265, 450, 875, 520, "error + retry", True)
    finish(p, "agent_flow")


def analysis_pipeline() -> None:
    p = svg_start("Automatic-analysis pipeline", "The deterministic report is the source of truth; provider-use flags remain false in the current engine.")
    box(p, 60, 330, 220, 145, "Uploaded frame", ["validated DataFrame"], SLATE)
    box(p, 380, 285, 250, 235, "DataUnderstandingEngine", ["domain / confidence", "grain / date", "dimensions", "measures / IDs"], PALE)
    box(p, 730, 285, 250, 235, "StatisticalPass", ["quality score", "aggregations", "periods", "chart specs"], "#ecfdf5", TEAL)
    box(p, 1080, 285, 250, 235, "DeterministicFallback", ["summary", "insight cards", "recommendations", "actions"], "#eff6ff", BLUE)
    box(p, 1390, 330, 155, 145, "Persist", ["report_json", "status"], SLATE)
    arrow(p, 280, 402, 380, 402)
    arrow(p, 630, 402, 730, 402)
    arrow(p, 980, 402, 1080, 402)
    arrow(p, 1330, 402, 1390, 402)
    p.append(f'<text x="735" y="620" font-family="Arial" font-size="18" fill="{MUTED}">Frontend renders executive summary, metrics, charts, warnings, evidence, and actions.</text>')
    finish(p, "analysis_pipeline")


def api_boundary() -> None:
    p = svg_start("API route and authentication boundary", "Every protected route passes through identity validation, owner lookup, and typed response handling.")
    box(p, 55, 320, 220, 155, "Browser", ["Bearer token", "JSON / multipart"], SLATE)
    box(p, 365, 250, 280, 295, "FastAPI route", ["parse request", "require_current_user", "rate limit", "get_dataset(owner_id)", "shape response"], PALE)
    box(p, 760, 155, 260, 150, "Auth service", ["JWT decode", "user lookup", "bcrypt login"], "#fefce8", ORANGE)
    box(p, 760, 375, 260, 150, "Owner-scoped registry", ["get / list / delete", "dataset_id + owner_id"], "#eff6ff", BLUE)
    box(p, 1160, 270, 320, 220, "Domain services", ["planner / analytics", "SQL / Pandas tools", "jobs / reports", "Pydantic contracts"], "#ecfdf5", TEAL)
    arrow(p, 275, 397, 365, 397, "request")
    arrow(p, 645, 335, 760, 230, "identity")
    arrow(p, 645, 440, 760, 450, "owner lookup")
    arrow(p, 1020, 450, 1160, 380, "authorized call")
    arrow(p, 1020, 230, 1160, 320, "valid user")
    p.append(f'<text x="365" y="650" font-family="Arial" font-size="18" fill="{MUTED}">Unauthorized requests stop at the dependency; a missing or cross-owner dataset is returned as HTTP 404.</text>')
    finish(p, "api_boundary")


def er_model() -> None:
    p = svg_start("Entity-relationship model", "SQLAlchemy entities and foreign-key relationships implemented in backend/app/database/models.py.")
    box(p, 55, 125, 300, 210, "users", ["PK id", "email UNIQUE", "hashed_password", "created_at"], PALE)
    box(p, 480, 95, 350, 270, "datasets", ["PK id", "FK owner_id → users", "filename / storage_key", "row_count", "column_schema", "created_at"], "#eff6ff", BLUE)
    box(p, 955, 95, 350, 270, "chat_sessions", ["PK id", "FK owner_id → users", "FK dataset_id → datasets", "created_at"], SLATE)
    box(p, 955, 510, 350, 260, "chat_messages", ["PK id", "FK session_id", "role / content", "analysis_data JSON", "created_at"], "#ecfdf5", TEAL)
    box(p, 480, 535, 350, 235, "auto_analysis_reports", ["PK/FK dataset_id", "FK owner_id → users", "report_json JSON", "gemini_used / groq_used", "updated_at"], "#fefce8", ORANGE)
    arrow(p, 355, 220, 480, 220, "owns")
    arrow(p, 355, 270, 955, 235, "owns")
    arrow(p, 830, 285, 955, 260, "contains")
    arrow(p, 1130, 365, 1130, 510, "contains")
    arrow(p, 655, 365, 655, 535, "cached report")
    p.append(f'<text x="55" y="835" font-family="Arial" font-size="17" fill="{MUTED}">Physical CSV payloads are stored through DatasetRegistry; the relational layer stores metadata and report/session records.</text>')
    finish(p, "er_model")


def job_states() -> None:
    p = svg_start("Background-job state transitions", "JobManager uses a four-worker in-process ThreadPoolExecutor and exposes status through GET /api/jobs/{id}.")
    box(p, 100, 350, 230, 145, "submit_job", ["create job_id", "status = processing"], PALE)
    box(p, 500, 350, 250, 145, "PROCESSING", ["worker executes fn", "record under lock"], "#fff7ed", ORANGE)
    box(p, 950, 190, 250, 145, "COMPLETED", ["result stored", "status returned"], "#ecfdf5", TEAL)
    box(p, 950, 510, 250, 145, "FAILED", ["error stored", "status returned"], "#fef2f2", "#b91c1c")
    arrow(p, 330, 422, 500, 422)
    arrow(p, 750, 390, 950, 260, "fn succeeds")
    arrow(p, 750, 455, 950, 580, "exception")
    p.append(f'<text x="1260" y="400" font-family="Arial" font-size="17" fill="{MUTED}">Owner ID is checked when a job is polled.</text>')
    finish(p, "job_states")


def deployment() -> None:
    p = svg_start("Deployment architecture and operational boundary", "Local evaluation is supported by SQLite; PostgreSQL and optional providers are configuration-dependent.")
    box(p, 55, 300, 260, 180, "Browser", ["Next.js UI", "local or hosted"], SLATE)
    box(p, 470, 240, 350, 300, "FastAPI backend", ["auth / routes", "analytics / tools", "JobManager", "structured logging"], PALE)
    box(p, 1050, 100, 300, 170, "SQLite / PostgreSQL", ["users / datasets", "sessions / reports"], SLATE)
    box(p, 1050, 350, 300, 170, "File storage", ["data/uploads/{id}.csv", "local volume"], "#eff6ff", BLUE)
    box(p, 1050, 600, 300, 170, "Optional services", ["Gemini", "Upstash Redis", "Upstash Vector"], "#fefce8", ORANGE)
    arrow(p, 315, 390, 470, 390, "HTTP / JSON")
    arrow(p, 820, 330, 1050, 185, "metadata")
    arrow(p, 820, 450, 1050, 435, "CSV payload")
    arrow(p, 820, 505, 1050, 685, "when configured", True)
    p.append(f'<text x="55" y="690" font-family="Arial" font-size="18" fill="{MUTED}">Not claimed: durable distributed workers, object storage, enterprise SSO, or compliance certification.</text>')
    finish(p, "deployment")


def main() -> None:
    architecture()
    context_dfd()
    upload_flow()
    structure_chart()
    agent_flow()
    analysis_pipeline()
    api_boundary()
    er_model()
    job_states()
    deployment()


if __name__ == "__main__":
    main()
