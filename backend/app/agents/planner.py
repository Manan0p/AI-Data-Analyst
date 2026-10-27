import json
import logging
import pandas as pd

from app.analytics.anomalies import AnomalyService
from app.analytics.auto_analysis import AutoAnalysisEngine
from app.analytics.profiler import ProfileService
from app.charts.factory import ChartFactory
from app.config import settings
from app.database.registry import DatasetRegistry
from app.schemas.contracts import AnalysisResponse
from app.analytics.understanding import DataUnderstandingEngine
from app.tools.pandas_tool import PandasTool
from app.tools.sql_tool import sql_tool

logger = logging.getLogger(__name__)


def _build_chart_from_rows(
    rows: list[dict],
    chart_type: str,
    x_hint: object = None,
    y_hint: object = None,
) -> dict | None:
    """Build a Plotly chart spec from SQL result rows.

    Automatically detects x (label/category column) and y (numeric column)
    if not provided explicitly via x_hint / y_hint.
    """
    if not rows:
        return None

    cols = list(rows[0].keys())
    if len(cols) < 1:
        return None

    # Determine x and y columns
    x_col = str(x_hint) if x_hint and str(x_hint) in cols else None
    y_col = str(y_hint) if y_hint and str(y_hint) in cols else None

    if x_col is None or y_col is None:
        # Auto-detect: first non-numeric col as x, first numeric as y
        for col in cols:
            sample = rows[0][col]
            if x_col is None and not isinstance(sample, (int, float)):
                x_col = col
            elif y_col is None and isinstance(sample, (int, float)):
                y_col = col
        # Fallback: use first two columns
        if x_col is None:
            x_col = cols[0]
        if y_col is None and len(cols) > 1:
            y_col = cols[1]

    x_vals = [row.get(x_col) for row in rows]
    y_vals = [row.get(y_col) for row in rows] if y_col else None

    if chart_type == "pie":
        trace = {
            "type": "pie",
            "labels": x_vals,
            "values": y_vals or [1] * len(x_vals),
        }
    else:
        trace = {"type": chart_type, "x": x_vals}
        if y_vals:
            trace["y"] = y_vals
        trace["name"] = y_col or x_col

    return {
        "data": [trace],
        "layout": {
            "title": f"{chart_type.title()}: {y_col or 'count'} by {x_col}",
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
        },
    }


# --------------------------------------------------------------------- #
#  Deterministic baseline planner (no LLM required)                      #
# --------------------------------------------------------------------- #
class PlannerAgent:
    def __init__(self):
        self.profile = ProfileService()
        self.anomalies = AnomalyService()
        self.charts = ChartFactory()
        self.auto_analysis = AutoAnalysisEngine()

    @staticmethod
    def _find_column(frame: pd.DataFrame, terms: tuple[str, ...], exclude: set[str] | None = None) -> str | None:
        exclude = exclude or set()
        ranked: list[tuple[int, str]] = []
        for col in frame.columns:
            name = str(col)
            if name in exclude:
                continue
            lowered = name.lower().replace("_", " ")
            score = sum(2 if term in lowered else 0 for term in terms)
            if score:
                ranked.append((score, name))
        return max(ranked, key=lambda item: item[0])[1] if ranked else None

    def _answer_business_question(self, dataset_id: str, frame: pd.DataFrame, message: str) -> AnalysisResponse | None:
        """Answer common business questions deterministically from validated evidence."""
        lower = message.lower()
        understanding = DataUnderstandingEngine().run(frame)
        working = understanding["frame"]
        metrics = understanding["metric_columns"]
        date_col = understanding.get("date_column")
        numeric = understanding.get("measures", [])
        revenue = metrics.get("revenue") or metrics.get("primary")
        profit = metrics.get("profit")

        if any(term in lower for term in ("executive summary", "key metrics", "overview", "what can you tell")):
            report = self.auto_analysis.run(dataset_id, working)
            return AnalysisResponse(
                answer=report.executive_summary,
                reasoning="The deterministic insight engine classified the dataset and grounded the summary in computed metrics.",
                confidence=0.94,
                assumptions=[f"Detected domain: {report.domain} ({report.domain_confidence:.0%} confidence)."],
                limitations=report.data_quality.warnings[:3],
                insights=[card.body for card in report.insights[:5]],
                metadata={"tool": "executive_summary", "planner": "deterministic", "report": report.model_dump()},
            )

        if any(term in lower for term in ("anomal", "outlier")):
            items = self.anomalies.detect(working)
            return AnalysisResponse(
                answer=f"Found {len(items)} potential anomalies across the meaningful numeric measures.",
                reasoning="Isolation Forest evaluated numeric measures after excluding identifier-like columns.",
                confidence=0.86,
                limitations=["Anomalies are statistical signals, not proof of business error."],
                anomalies=items,
                metadata={"tool": "anomaly", "planner": "deterministic"},
            )

        if any(term in lower for term in ("profile", "null", "missing", "duplicate", "schema")):
            p = self.profile.profile(dataset_id, working)
            return AnalysisResponse(
                answer=f"This dataset contains {p.rows:,} {understanding['grain']} records across {p.columns} columns, with {p.duplicate_rows:,} duplicate rows.",
                reasoning="The dataset understanding layer inspected structure, grain, missingness, and meaningful column types.",
                confidence=0.98,
                limitations=["Column semantics are inferred from names, types, and distributions."],
                metadata={"tool": "profile", "planner": "deterministic", "profile": p.model_dump(), "understanding": {k: v for k, v in understanding.items() if k != "frame"}},
            )

        is_time_query = any(term in lower for term in ("monthly", "month", "over time", "trend", "peak period", "worst period"))

        # Ranking questions: “top products/categories/regions by sales/profit”.
        if not is_time_query and any(term in lower for term in ("top", "highest", "best", "lowest", "worst")):
            if "categor" in lower:
                preferred_dimension_terms = ["sub-category", "category"] if "sub-category" in lower else ["category", "sub-category"]
            elif "product" in lower:
                preferred_dimension_terms = ["product"]
            else:
                preferred_dimension_terms = [
                    term for term in ("region", "state", "city", "segment", "channel", "campaign", "customer")
                    if term in lower
                ]
            dimension = None
            for term in preferred_dimension_terms:
                normalized_term = term.lower().replace("_", " ")
                dimension = next((col for col in understanding["dimensions"] if col.lower().replace("_", " ").strip() == normalized_term), None)
                if not dimension:
                    dimension = next((col for col in understanding["dimensions"] if term in col.lower()), None)
                if dimension:
                    break
            dimension = dimension or (understanding["dimensions"][0] if understanding["dimensions"] else None)
            measure = profit if any(term in lower for term in ("profit", "margin")) else revenue
            if measure is None:
                measure = numeric[0] if numeric else None
            if dimension and measure:
                temp = working[[dimension, measure]].copy()
                temp[measure] = pd.to_numeric(temp[measure], errors="coerce")
                grouped = temp.dropna().groupby(dimension)[measure].agg(["sum", "mean", "count"])
                descending = not any(term in lower for term in ("lowest", "worst"))
                grouped = grouped.sort_values("sum", ascending=not descending).head(5)
                rows = [{dimension: str(idx), f"total_{measure}": float(row["sum"]), "records": int(row["count"])} for idx, row in grouped.iterrows()]
                direction = "highest" if descending else "lowest"
                answer = f"The {direction} {measure} values are led by {rows[0][dimension]} at {rows[0][f'total_{measure}']:,.2f}."
                chart = _build_chart_from_rows(rows, "bar", x_hint=dimension, y_hint=f"total_{measure}")
                return AnalysisResponse(
                    answer=answer,
                    reasoning=f"Grouped {measure} by {dimension}, sorted by total, and returned the top five groups.",
                    confidence=0.97,
                    generated_sql=f"SELECT {dimension}, SUM({measure}) AS total_{measure}, COUNT(*) AS records FROM {DatasetRegistry.table_name(dataset_id)} GROUP BY {dimension} ORDER BY total_{measure} {'DESC' if descending else 'ASC'} LIMIT 5",
                    chart=chart,
                    data=rows,
                    metadata={"tool": "sql", "planner": "deterministic", "rows": rows, "dimension": dimension, "measure": measure},
                )

        if is_time_query and date_col and revenue:
            temp = working[[date_col, revenue] + ([profit] if profit else [])].copy()
            temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
            for col in [revenue, profit]:
                if col:
                    temp[col] = pd.to_numeric(temp[col], errors="coerce")
            temp = temp.dropna(subset=[date_col, revenue])
            temp["period"] = temp[date_col].dt.to_period("M").astype(str)
            grouped = temp.groupby("period").agg(**{"sales": (revenue, "sum"), **({"profit": (profit, "sum")} if profit else {})}).sort_index()
            if not grouped.empty:
                peak = grouped["sales"].idxmax()
                worst = grouped["sales"].idxmin()
                rows = [{"period": idx, **{key: float(value) for key, value in row.items()}} for idx, row in grouped.iterrows()]
                chart = _build_chart_from_rows(rows, "line", x_hint="period", y_hint="sales")
                return AnalysisResponse(
                    answer=f"Peak sales occurred in {peak} at {grouped.loc[peak, 'sales']:,.2f}; the weakest month was {worst} at {grouped.loc[worst, 'sales']:,.2f}.",
                    reasoning=f"Parsed {date_col} as the primary time column and aggregated {revenue} monthly.",
                    confidence=0.96,
                    chart=chart,
                    data=rows,
                    metadata={"tool": "trend", "planner": "deterministic", "rows": rows, "date_column": date_col},
                )

        return None

    def respond(self, dataset_id: str, frame: pd.DataFrame, message: str) -> AnalysisResponse:
        business_response = self._answer_business_question(dataset_id, frame, message)
        if business_response is not None:
            return business_response
        prompt = message.lower()
        if any(w in prompt for w in ("anomal", "outlier")):
            items = self.anomalies.detect(frame)
            return AnalysisResponse(
                answer=f"Found {len(items)} potential anomalies.",
                reasoning="The fallback planner selected Isolation Forest because the question asks for anomalous observations.",
                confidence=0.82,
                assumptions=["Numeric columns are comparable after Isolation Forest preprocessing."],
                limitations=["Small and categorical-only datasets may not be detected."],
                anomalies=items,
                metadata={"tool": "anomaly", "planner": "deterministic"},
            )
        if any(w in prompt for w in ("profile", "null", "column", "dataset")):
            p = self.profile.profile(dataset_id, frame)
            return AnalysisResponse(
                answer=f"{p.rows:,} rows, {p.columns} columns, and {p.duplicate_rows:,} duplicate rows.",
                reasoning="The fallback planner selected data profiling based on the request.",
                confidence=0.99,
                metadata={"tool": "profile", "planner": "deterministic", "profile": p.model_dump()},
            )
        report = self.auto_analysis.run(dataset_id, frame)
        answer = report.executive_summary
        return AnalysisResponse(
            answer=answer,
            reasoning="The fallback planner used the semantic dataset understanding and deterministic insight engine instead of treating every numeric column as a business measure.",
            confidence=0.9,
            assumptions=[f"Detected domain: {report.domain} ({report.domain_confidence:.0%} confidence)."],
            limitations=report.data_quality.warnings[:3],
            insights=[card.body for card in report.insights[:5]],
            metadata={"tool": "executive_summary", "planner": "deterministic", "report": report.model_dump()},
        )


# --------------------------------------------------------------------- #
#  Gemini-powered planner                                                 #
# --------------------------------------------------------------------- #
class GeminiPlannerAgent(PlannerAgent):

    TOOLS = {"sql", "pandas", "chart", "profile", "anomaly", "statistics"}

    def __init__(self):
        super().__init__()
        from app.agents.graph import create_agent_graph
        self.graph = create_agent_graph()

    @staticmethod
    def _list(value: object) -> list[str]:
        return value if isinstance(value, list) and all(isinstance(x, str) for x in value) else []

    def _schema(self, datasets: dict[str, pd.DataFrame]) -> str:
        tables = []
        for table, frame in datasets.items():
            cols = []
            for c in frame.columns:
                dtype = str(frame[c].dtype)
                # Map pandas dtypes to friendly SQL types for Gemini
                if "datetime" in dtype:
                    sql_type = "TIMESTAMP"
                elif dtype.startswith("int") or dtype.startswith("uint"):
                    sql_type = "INTEGER"
                elif dtype.startswith("float"):
                    sql_type = "DOUBLE"
                else:
                    sql_type = "VARCHAR"
                cols.append({
                    "name": str(c),
                    "dtype": dtype,
                    "sql_type": sql_type,
                    "sample_values": frame[c].dropna().head(3).astype(str).tolist(),
                })
            tables.append({"table": table, "rows": len(frame), "columns": cols})
        return json.dumps(tables)

    def respond_with_context(
        self,
        primary_id: str,
        datasets: dict[str, pd.DataFrame],
        message: str,
        history: list[dict[str, str]],
        rag_context: list[dict[str, str]] | None = None,
    ) -> AnalysisResponse:
        primary_key = DatasetRegistry.table_name(primary_id)
        primary = datasets.get(primary_key)
        if primary is None:
            primary = next(iter(datasets.values())) if datasets else pd.DataFrame()

        # Prefer grounded deterministic answers for common business questions.
        # This prevents provider latency/outages from turning a clear request
        # into a generic numeric-average response.
        deterministic = self._answer_business_question(primary_id, primary, message)
        if deterministic is not None:
            return deterministic

        if not settings.gemini_api_key:
            return self.respond(primary_id, primary, message)

        try:
            schema_data = json.loads(self._schema(datasets))

            # ── Build enriched message list ─────────────────────────────────
            # Order: [RAG semantic context] + [recent turns] + [current user msg]
            messages: list[dict] = []

            if rag_context:
                # Inject a synthetic system note so the LLM understands the source
                messages.append({
                    "role": "user",
                    "content": (
                        "[Context: the following turns from earlier in this conversation "
                        "are semantically relevant to the current question]\n"
                        + "\n".join(
                            f"{t['role'].upper()}: {t['content']}"
                            for t in rag_context
                        )
                    ),
                })
                messages.append({
                    "role": "model",
                    "content": "Understood. I will use this context when answering.",
                })

            messages.extend(history)
            messages.append({"role": "user", "content": message})

            initial_state = {
                "messages": messages,
                "dataset_id": primary_id,
                "schema": schema_data,
                "intent": None,
                "tool": None,
                "tool_args": None,
                "tool_result": None,
                "error": None,
                "retries": 0,
                "final_answer": None,
                "datasets": datasets,
            }
            final_state = self.graph.invoke(initial_state)
            ans = final_state.get("final_answer")
            if ans and isinstance(ans, dict):
                return AnalysisResponse(**ans)
            elif isinstance(ans, AnalysisResponse):
                return ans
            return self.respond(primary_id, primary, message)
        except Exception as exc:
            logger.warning("LangGraph agent execution failed, triggering safety fallback: %s", exc)
            response = self.respond(primary_id, primary, message)
            response.metadata["planner_fallback"] = "langgraph_failure"
            response.metadata["error"] = str(exc)
            return response

