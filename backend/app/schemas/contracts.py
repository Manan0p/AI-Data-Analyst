from typing import Any
from pydantic import BaseModel, Field
class DatasetSummary(BaseModel): id: str; name: str; rows: int; columns: int; preview: list[dict[str, Any]]
class ProfileResponse(BaseModel): dataset_id: str; rows: int; columns: int; duplicate_rows: int; columns_profile: list[dict[str, Any]]; numeric_summary: dict[str, dict[str, float | None]]
class AnalysisResponse(BaseModel):
    answer: str; reasoning: str; confidence: float = Field(ge=0, le=1); assumptions: list[str] = []; limitations: list[str] = []; generated_sql: str | None = None; generated_pandas: str | None = None; chart: dict[str, Any] | None = None; insights: list[str] = []; anomalies: list[dict[str, Any]] = []; metadata: dict[str, Any] = {}
class ChatRequest(BaseModel): dataset_id: str; message: str = Field(min_length=1, max_length=4000); session_id: str = "default"
class SqlRequest(BaseModel): dataset_id: str; query: str
class ChartRequest(BaseModel): dataset_id: str; chart_type: str; x: str; y: str | None = None
class PandasRequest(BaseModel): dataset_id: str; code: str
