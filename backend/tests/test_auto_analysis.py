import pandas as pd
import pytest
from app.analytics.auto_analysis import (
    AutoAnalysisEngine,
    StatisticalPass,
    DeterministicFallback,
    _safe,
    _top_n,
)
from app.schemas.contracts import AutoAnalysisResponse


def test_safe_helper():
    assert _safe(10.5) == 10.5
    assert _safe(float("nan")) is None
    assert _safe(float("inf")) is None
    assert _safe("hello") == "hello"


def test_top_n_helper():
    series = pd.Series(["A", "A", "B", "C", "A", "B"])
    top = _top_n(series, n=2)
    assert len(top) == 2
    assert top[0] == {"label": "A", "value": 3}
    assert top[1] == {"label": "B", "value": 2}


def test_statistical_pass():
    df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "category": ["Electronics", "Clothing", "Electronics", "Home"],
        "revenue": [100.0, 50.0, 150.0, 80.0],
        "quantity": [2, 1, 3, 2]
    })
    stat_pass = StatisticalPass()
    res = stat_pass.run("test_ds", df)

    assert "quality" in res
    assert "stats" in res
    assert "charts" in res
    assert "top_n" in res
    assert res["quality"].total_rows == 4
    assert res["quality"].total_columns == 4
    assert res["quality"].duplicate_rows == 0
    assert "revenue" in res["stats"]
    assert "category" in res["top_n"]
    assert len(res["charts"]) > 0


def test_deterministic_fallback():
    df = pd.DataFrame({
        "category": ["A", "B", "A", "C"],
        "sales": [100.0, 200.0, 300.0, 400.0]
    })
    stat_pass = StatisticalPass()
    stat_res = stat_pass.run("test_ds", df)
    fallback = DeterministicFallback()
    res = fallback.build(df, stat_res["stats"], stat_res["top_n"], stat_res["quality"])

    assert "executive_summary" in res
    assert "insight_cards" in res
    assert "recommendations" in res
    assert "trend_story" in res
    assert len(res["insight_cards"]) >= 1
    assert len(res["recommendations"]) >= 1


def test_auto_analysis_engine_offline():
    """Test full engine run in offline fallback mode (no API keys or simulated fallback)."""
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West", "North"],
        "profit": [1000, 2500, -500, 1800, 2200],
        "units": [10, 25, 5, 18, 22]
    })
    engine = AutoAnalysisEngine()
    result = engine.run("dataset_123", df)

    assert isinstance(result, AutoAnalysisResponse)
    assert result.dataset_id == "dataset_123"
    assert result.status == "completed"
    assert len(result.executive_summary) > 0
    assert len(result.insights) > 0
    assert result.data_quality.total_rows == 5
    assert result.data_quality.total_columns == 3
