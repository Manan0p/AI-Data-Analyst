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

class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    result: Any | None = None
    error: str | None = None


# ── Auto-Analysis schemas ────────────────────────────────────────────────────

class InsightCard(BaseModel):
    title: str
    body: str
    metric: str | None = None          # big display value e.g. "42%" or "$1.2M"
    type: str = "stat"                 # stat | trend | anomaly | distribution | correlation
    chart: dict[str, Any] | None = None
    importance: float = 0.5            # 0.0 – 1.0, used for sort order

class DataQualityReport(BaseModel):
    total_rows: int
    total_columns: int
    duplicate_rows: int
    null_columns: list[dict[str, Any]] = []   # [{name, null_pct}] sorted desc
    healthy_columns: int = 0
    health_score: float = 100.0               # 0 – 100

class AutoAnalysisResponse(BaseModel):
    dataset_id: str
    executive_summary: str
    trend_story: str | None = None
    insights: list[InsightCard] = []
    charts: list[dict[str, Any]] = []
    recommendations: list[str] = []
    data_quality: DataQualityReport
    anomaly_note: str | None = None
    generated_at: str
    gemini_used: bool = False
    groq_used: bool = False
    status: str = "completed"          # completed | processing | failed
