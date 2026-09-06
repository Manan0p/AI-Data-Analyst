import json
import logging
from typing import Any, Literal
import pandas as pd
from langgraph.graph import END, StateGraph

from app.agents.state import AgentState
from app.analytics.anomalies import AnomalyService
from app.analytics.profiler import ProfileService
from app.charts.factory import ChartFactory
from app.config import settings
from app.database.registry import DatasetRegistry
from app.schemas.contracts import AnalysisResponse
from app.tools.pandas_tool import PandasTool
from app.tools.sql_tool import sql_tool

logger = logging.getLogger(__name__)


def _extract_last_message(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, dict):
        return last.get("content", str(last))
    if hasattr(last, "content"):
        return str(last.content)
    return str(last)


def _get_primary_frame(state: AgentState) -> pd.DataFrame:
    datasets = state.get("datasets", {})
    primary_key = DatasetRegistry.table_name(state["dataset_id"])
    if primary_key in datasets:
        return datasets[primary_key]
    if datasets:
        return next(iter(datasets.values()))
    return pd.DataFrame()


def classify_intent(state: AgentState) -> dict[str, Any]:
    """Classify the user message into an analytical intent."""
    msg = _extract_last_message(state).lower()

    if any(w in msg for w in ("plot", "chart", "graph", "visualize", "trend chart", "histogram", "bar chart")):
        intent = "visualization"
    elif any(w in msg for w in ("anomal", "outlier")):
        intent = "anomaly"
    elif any(w in msg for w in ("profile", "null", "missing", "duplicate", "schema", "column info")):
        intent = "profiling"
    elif any(w in msg for w in ("python", "pandas", "series", "dataframe", "filter", "head")):
        intent = "computation"
    else:
        intent = "query"

    return {"intent": intent}


def select_tool(state: AgentState) -> dict[str, Any]:
    """Select the tool and generate its invocation arguments."""
    intent = state.get("intent", "query")
    error = state.get("error")
    msg = _extract_last_message(state)
    primary_frame = _get_primary_frame(state)
    datasets = state.get("datasets", {})
    primary_table = DatasetRegistry.table_name(state["dataset_id"])

    # If Gemini API key is available, use LLM for tool selection and argument formulation
    if settings.gemini_api_key:
        try:
            from google import genai
            from google.genai import types

            error_feedback = ""
            if error:
                error_feedback = (
                    f"\n[ATTENTION: Previous tool execution failed with error: '{error}'. "
                    "Analyze this error carefully, inspect the schema below, and fix the query/arguments.]\n"
                )

            system = (
                "You are an expert data analyst. Return valid JSON only with these exact keys: "
                "tool, sql, pandas, chart_type, x, y, answer, reasoning, confidence, assumptions, limitations.\n\n"
                "## Tool Selection Rules:\n"
                "- 'sql': For metrics, aggregations, counts, filters, top-N, math calculations.\n"
                "- 'pandas': For complex pandas expressions.\n"
                "- 'chart': When user asks to plot, chart, or graph.\n"
                "- 'profile': For dataset structural inquiries (rows, columns, nulls, duplicates).\n"
                "- 'anomaly': For outlier/anomaly detection.\n"
                "- 'statistics': For general descriptive statistics without SQL.\n"
                f"{error_feedback}"
            )

            prompt = (
                f"{system}\n"
                f"<schema>{json.dumps(state.get('schema', {}))}</schema>\n"
                f"<question>{msg}</question>"
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            plan = json.loads(response.text)
            chosen_tool = plan.get("tool", "sql")
            tool_args = {
                "sql": plan.get("sql", f"SELECT * FROM {primary_table} LIMIT 10"),
                "code": plan.get("pandas", "df.head(10)"),
                "chart_type": plan.get("chart_type", "bar"),
                "x": plan.get("x", ""),
                "y": plan.get("y", None),
                "answer": plan.get("answer", "Analysis executed."),
                "reasoning": plan.get("reasoning", f"Selected {chosen_tool} tool."),
                "confidence": plan.get("confidence", 0.85),
            }
            return {"tool": chosen_tool, "tool_args": tool_args}
        except Exception as llm_exc:
            logger.warning("LLM tool selection failed, using rule-based selection: %s", llm_exc)

    # Deterministic fallback tool selection (used when offline or if LLM encounters issues)
    cols = list(primary_frame.columns)
    if intent == "visualization":
        x_col = cols[0] if cols else "x"
        y_col = cols[1] if len(cols) > 1 else None
        return {
            "tool": "chart",
            "tool_args": {"chart_type": "bar", "x": x_col, "y": y_col, "sql": f"SELECT * FROM {primary_table} LIMIT 50"}
        }
    elif intent == "anomaly":
        return {"tool": "anomaly", "tool_args": {}}
    elif intent == "profiling":
        return {"tool": "profile", "tool_args": {}}
    elif intent == "computation":
        return {"tool": "pandas", "tool_args": {"code": "df.head(10)"}}
    else:
        return {
            "tool": "sql",
            "tool_args": {"sql": f"SELECT * FROM {primary_table} LIMIT 10"}
        }


def execute_tool(state: AgentState) -> dict[str, Any]:
    """Execute the chosen tool deterministically."""
    tool = state.get("tool", "sql")
    args = state.get("tool_args", {})
    primary_frame = _get_primary_frame(state)
    datasets = state.get("datasets", {})
    primary_id = state["dataset_id"]

    try:
        if tool == "sql":
            query = args.get("sql", "")
            if not query:
                raise ValueError("No SQL query provided for sql tool execution.")
            clean_query, rows = sql_tool.run(datasets, query)
            result = {"sql": clean_query, "rows": rows}

        elif tool == "pandas":
            code = args.get("code", "")
            if not code:
                raise ValueError("No pandas code provided for pandas tool execution.")
            rows = PandasTool().run(primary_frame, code)
            result = {"code": code, "rows": rows}

        elif tool == "chart":
            chart_type = args.get("chart_type", "bar")
            x = args.get("x", "")
            y = args.get("y", None)
            chart_spec = ChartFactory().create(primary_frame, chart_type, x, y)
            result = {"chart": chart_spec}

        elif tool == "profile":
            profile_data = ProfileService().profile(primary_id, primary_frame).model_dump()
            result = {"profile": profile_data}

        elif tool == "anomaly":
            anomalies = AnomalyService().detect(primary_frame)
            result = {"anomalies": anomalies}

        else:
            # Descriptive statistics
            num = primary_frame.select_dtypes(include="number")
            desc = num.mean().to_dict() if not num.empty else {}
            result = {"statistics": desc}

        return {"tool_result": result, "error": None}

    except Exception as exc:
        logger.info("Tool %s failed with error: %s", tool, exc)
        return {"error": str(exc), "tool_result": None}


def validate_result(state: AgentState) -> Literal["select_tool", "synthesize_answer", "fallback_deterministic"]:
    """Conditional edge validating the tool outcome and deciding on retries or fallbacks."""
    error = state.get("error")
    retries = state.get("retries", 0)

    if error:
        if retries < 2:
            state["retries"] = retries + 1
            logger.info("Validation failed: retrying (attempt %d of 2) with error: %s", state["retries"], error)
            return "select_tool"
        logger.warning("Validation failed: retries exhausted after %d attempts. Triggering deterministic fallback.", retries)
        return "fallback_deterministic"

    return "synthesize_answer"


def synthesize_answer(state: AgentState) -> dict[str, Any]:
    """Format successful tool results into an AnalysisResponse."""
    tool = state.get("tool", "unknown")
    result = state.get("tool_result", {})
    args = state.get("tool_args", {})
    retries = state.get("retries", 0)

    reasoning = args.get("reasoning", f"Executed {tool} successfully with validated result.")
    confidence = float(args.get("confidence", 0.9))

    final_resp = AnalysisResponse(
        answer=str(args.get("answer") or f"Analysis completed using {tool}."),
        reasoning=reasoning,
        confidence=confidence,
        generated_sql=result.get("sql") if isinstance(result, dict) else None,
        generated_pandas=result.get("code") if isinstance(result, dict) else None,
        chart=result.get("chart") if isinstance(result, dict) else None,
        anomalies=result.get("anomalies", []) if isinstance(result, dict) else [],
        metadata={
            "tool": tool,
            "planner": "langgraph",
            "retries": retries,
            "rows": result.get("rows") if isinstance(result, dict) else None,
            "profile": result.get("profile") if isinstance(result, dict) else None,
        },
    )
    return {"final_answer": final_resp.model_dump()}


def fallback_deterministic(state: AgentState) -> dict[str, Any]:
    """Circuit-breaker deterministic fallback."""
    from app.agents.planner import PlannerAgent
    primary_frame = _get_primary_frame(state)
    msg = _extract_last_message(state)
    dataset_id = state.get("dataset_id", "")

    fallback_agent = PlannerAgent()
    resp = fallback_agent.respond(dataset_id, primary_frame, msg)
    resp.metadata["planner_fallback"] = "langgraph_retry_exhausted"
    resp.metadata["last_error"] = state.get("error")
    resp.metadata["retries"] = state.get("retries", 0)

    return {"final_answer": resp.model_dump()}


def create_agent_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("select_tool", select_tool)
    workflow.add_node("execute_tool", execute_tool)
    workflow.add_node("synthesize_answer", synthesize_answer)
    workflow.add_node("fallback_deterministic", fallback_deterministic)

    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "select_tool")
    workflow.add_edge("select_tool", "execute_tool")

    workflow.add_conditional_edges(
        "execute_tool",
        validate_result,
        {
            "select_tool": "select_tool",
            "synthesize_answer": "synthesize_answer",
            "fallback_deterministic": "fallback_deterministic",
        },
    )

    workflow.add_edge("synthesize_answer", END)
    workflow.add_edge("fallback_deterministic", END)

    return workflow.compile()
