import json
import logging
import pandas as pd

from app.analytics.anomalies import AnomalyService
from app.analytics.profiler import ProfileService
from app.charts.factory import ChartFactory
from app.config import settings
from app.database.registry import DatasetRegistry
from app.schemas.contracts import AnalysisResponse
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

    def respond(self, dataset_id: str, frame: pd.DataFrame, message: str) -> AnalysisResponse:
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
        numeric = frame.select_dtypes(include="number")
        if numeric.empty:
            answer = f"{len(frame):,} rows are available. Ask about a specific column to analyse it."
        else:
            top = numeric.mean().sort_values(ascending=False).index[0]
            answer = f"The largest numeric average is **{top}** at {numeric[top].mean():,.2f}."
        return AnalysisResponse(
            answer=answer,
            reasoning="The fallback planner selected descriptive statistics as the safest fit for this general question.",
            confidence=0.74,
            assumptions=["Column means are meaningful for the question."],
            limitations=["No semantic business definitions were provided."],
            insights=[answer],
            metadata={"tool": "statistics", "planner": "deterministic"},
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
    ) -> AnalysisResponse:
        primary_key = DatasetRegistry.table_name(primary_id)
        primary = datasets.get(primary_key)
        if primary is None:
            primary = next(iter(datasets.values())) if datasets else pd.DataFrame()

        if not settings.gemini_api_key:
            return self.respond(primary_id, primary, message)

        try:
            schema_data = json.loads(self._schema(datasets))
            initial_state = {
                "messages": history + [{"role": "user", "content": message}],
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

