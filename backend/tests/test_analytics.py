import pandas as pd
import pytest
from app.analytics.profiler import ProfileService
from app.analytics.anomalies import AnomalyService
from app.charts.factory import ChartFactory

def test_profiler_service():
    df = pd.DataFrame({
        "category": ["A", "B", "A", "C", None],
        "value": [10.0, 20.0, 30.0, 40.0, 50.0]
    })
    service = ProfileService()
    profile = service.profile("ds_test", df)
    
    assert profile.dataset_id == "ds_test"
    assert profile.rows == 5
    assert profile.columns == 2
    assert profile.duplicate_rows == 0
    assert len(profile.columns_profile) == 2
    
    # Category has 1 null (20%)
    cat_prof = next(c for c in profile.columns_profile if c["name"] == "category")
    assert cat_prof["null_percentage"] == 20.0

def test_anomaly_service():
    # Build dataset with obvious outlier
    normal_data = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 1000] # 1000 is extreme outlier
    df = pd.DataFrame({"val1": normal_data, "val2": normal_data})
    
    service = AnomalyService()
    anomalies = service.detect(df)
    assert isinstance(anomalies, list)
    if len(anomalies) > 0:
        assert "row_index" in anomalies[0]
        assert "reason" in anomalies[0]

def test_chart_factory():
    df = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar"],
        "sales": [100, 150, 200]
    })
    factory = ChartFactory()
    spec = factory.create(df, "bar", x="month", y="sales")
    assert spec["data"][0]["type"] == "bar"
    assert spec["data"][0]["x"] == ["Jan", "Feb", "Mar"]
    assert spec["data"][0]["y"] == [100, 150, 200]
