import pandas as pd
import pytest
from app.agents.graph import create_agent_graph, validate_result
from app.database.registry import DatasetRegistry


@pytest.fixture
def sample_data():
    df = pd.DataFrame({
        "product": ["Alpha", "Beta", "Gamma"],
        "sales": [100.0, 250.0, 300.0],
        "quantity": [2, 5, 6]
    })
    table_name = DatasetRegistry.table_name("test_ds")
    return {"test_ds": df, "datasets": {table_name: df}}


def test_graph_compiles():
    graph = create_agent_graph()
    assert graph is not None


def test_validate_result_state_transitions():
    # 1. Success path
    state_ok = {"error": None, "retries": 0}
    assert validate_result(state_ok) == "synthesize_answer"

    # 2. First failure -> retry 1
    state_err1 = {"error": "syntax error near SELECT", "retries": 0}
    next_node = validate_result(state_err1)
    assert next_node == "select_tool"
    assert state_err1["retries"] == 1

    # 3. Second failure -> retry 2
    state_err2 = {"error": "syntax error near SELECT", "retries": 1}
    next_node = validate_result(state_err2)
    assert next_node == "select_tool"
    assert state_err2["retries"] == 2

    # 4. Third failure (retries >= 2) -> circuit breaker fallback
    state_err3 = {"error": "syntax error near SELECT", "retries": 2}
    next_node = validate_result(state_err3)
    assert next_node == "fallback_deterministic"


def test_graph_executes_sql_flow(sample_data):
    graph = create_agent_graph()
    initial_state = {
        "messages": [{"role": "user", "content": "Show me total sales"}],
        "dataset_id": "test_ds",
        "schema": {},
        "intent": None,
        "tool": None,
        "tool_args": None,
        "tool_result": None,
        "error": None,
        "retries": 0,
        "final_answer": None,
        "datasets": sample_data["datasets"],
    }

    result_state = graph.invoke(initial_state)
    assert result_state["final_answer"] is not None
    answer = result_state["final_answer"]
    assert "metadata" in answer
    assert answer["metadata"]["tool"] == "sql"
    assert answer["metadata"]["planner"] == "langgraph"


def test_graph_executes_profiling_flow(sample_data):
    graph = create_agent_graph()
    initial_state = {
        "messages": [{"role": "user", "content": "profile this dataset schema and null count"}],
        "dataset_id": "test_ds",
        "schema": {},
        "intent": None,
        "tool": None,
        "tool_args": None,
        "tool_result": None,
        "error": None,
        "retries": 0,
        "final_answer": None,
        "datasets": sample_data["datasets"],
    }

    result_state = graph.invoke(initial_state)
    assert result_state["final_answer"] is not None
    assert result_state["final_answer"]["metadata"]["tool"] == "profile"


def test_graph_executes_anomaly_flow(sample_data):
    graph = create_agent_graph()
    initial_state = {
        "messages": [{"role": "user", "content": "detect any anomalies or outliers"}],
        "dataset_id": "test_ds",
        "schema": {},
        "intent": None,
        "tool": None,
        "tool_args": None,
        "tool_result": None,
        "error": None,
        "retries": 0,
        "final_answer": None,
        "datasets": sample_data["datasets"],
    }

    result_state = graph.invoke(initial_state)
    assert result_state["final_answer"] is not None
    assert result_state["final_answer"]["metadata"]["tool"] == "anomaly"


def test_graph_exhausted_retries_triggers_fallback(sample_data):
    # Simulate a failing tool call that continuously raises errors until retries exhaust
    graph = create_agent_graph()
    initial_state = {
        "messages": [{"role": "user", "content": "run bad sql"}],
        "dataset_id": "test_ds",
        "schema": {},
        "intent": "query",
        "tool": "sql",
        "tool_args": {"sql": "SELECT * FROM non_existent_table_xyz"},
        "tool_result": None,
        "error": "Table does not exist",
        "retries": 2,  # Already at retry limit
        "final_answer": None,
        "datasets": sample_data["datasets"],
    }

    # Calling directly from validate_result -> fallback_deterministic
    next_step = validate_result(initial_state)
    assert next_step == "fallback_deterministic"
