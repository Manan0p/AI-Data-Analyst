import pandas as pd

from app.agents.planner import PlannerAgent
from app.analytics.auto_analysis import AutoAnalysisEngine
from app.analytics.understanding import DataUnderstandingEngine


def test_understanding_excludes_identifier_like_numeric_columns():
    frame = pd.DataFrame({
        "Row ID": [1, 2, 3],
        "Postal Code": [10001, 10002, 10003],
        "Category": ["A", "B", "A"],
        "Sales": [10.0, 20.0, 30.0],
    })
    model = DataUnderstandingEngine().run(frame)
    assert "Row ID" in model["identifiers"]
    assert "Postal Code" in model["identifiers"]
    assert "Sales" in model["measures"]
    assert model["metric_columns"]["revenue"] == "Sales"


def test_auto_analysis_has_domain_aware_sales_findings():
    frame = pd.DataFrame({
        "Order Date": ["2024-01-01", "2024-01-02", "2024-02-01", "2024-02-02"],
        "Category": ["Technology", "Furniture", "Technology", "Furniture"],
        "Product Name": ["Good", "Loss", "Good", "Loss"],
        "Sales": [100, 200, 150, 250],
        "Profit": [40, -20, 60, -30],
        "Discount": [0.0, 0.8, 0.0, 0.8],
    })
    report = AutoAnalysisEngine().run("sales_fixture", frame)
    assert report.domain == "sales"
    assert report.grain in {"row", "order line"}
    assert any("profit" in insight.title.lower() for insight in report.insights)
    assert report.recommendations


def test_chat_fallback_answers_category_question_with_category_not_postal_code():
    frame = pd.DataFrame({
        "Row ID": [1, 2, 3, 4],
        "Postal Code": [10001, 10002, 10003, 10004],
        "Category": ["Technology", "Furniture", "Technology", "Office Supplies"],
        "Sales": [100, 200, 300, 50],
    })
    response = PlannerAgent().respond("fixture", frame, "What are the top product categories by sales?")
    assert response.metadata["dimension"] == "Category"
    assert "Postal Code" not in response.answer
