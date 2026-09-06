import logging
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from app.agents.planner import GeminiPlannerAgent
from app.analytics.anomalies import AnomalyService
from app.analytics.profiler import ProfileService
from app.charts.factory import ChartFactory
from app.core.limiter import limiter
from app.database.registry import registry
from app.memory.session import memory
from app.schemas.contracts import *
from app.services.auth import get_current_user
from app.services.ingestion import CsvIngestionService
from app.services.jobs import job_manager
from app.tools.pandas_tool import PandasTool
from app.tools.sql_tool import sql_tool

router = APIRouter()
ingestion = CsvIngestionService(registry)
profiler = ProfileService()
planner = GeminiPlannerAgent()
logger = logging.getLogger(__name__)

def get_dataset(dataset_id: str, owner_id: str | None = None):
    try:
        return registry.get(dataset_id, owner_id=owner_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc

def summary(d):
    return DatasetSummary(
        id=d.id,
        name=d.name,
        rows=len(d.frame),
        columns=len(d.frame.columns),
        preview=d.frame.head(10).where(d.frame.notna(), None).to_dict(orient='records')
    )

@router.post('/upload', response_model=list[DatasetSummary])
@limiter.limit("10/minute")
async def upload(
    request: Request,
    files: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    return [summary(await ingestion.ingest(f, owner_id=current_user)) for f in files]

@router.post('/upload/async', response_model=JobResponse, status_code=202)
@limiter.limit("10/minute")
async def upload_async(
    request: Request,
    files: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    file_payloads = []
    for f in files:
        content = await f.read()
        file_payloads.append((f.filename or "upload.csv", content))

    def _task():
        results = []
        for fname, content in file_payloads:
            ds = ingestion.ingest_bytes(fname, content, owner_id=current_user)
            results.append(summary(ds).model_dump())
        return results

    job_id = job_manager.submit_job("csv_ingestion", current_user, _task)
    return JobResponse(job_id=job_id, job_type="csv_ingestion", status="processing")

@router.get('/jobs/{job_id}', response_model=JobResponse)
def get_job(job_id: str, current_user: str = Depends(get_current_user)):
    job = job_manager.get_job(job_id, user_id=current_user)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return JobResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status.value,
        result=job.result,
        error=job.error,
    )


@router.get('/datasets', response_model=list[DatasetSummary])
def datasets(current_user: str = Depends(get_current_user)):
    return [summary(d) for d in registry.list(owner_id=current_user)]

@router.delete('/datasets/{dataset_id}')
def delete_dataset(dataset_id: str, current_user: str = Depends(get_current_user)):
    if not registry.delete(dataset_id, owner_id=current_user):
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")
    return {"message": "Dataset deleted"}

@router.delete('/datasets')
def delete_all_datasets(current_user: str = Depends(get_current_user)):
    registry.clear(owner_id=current_user)
    return {"message": "All user datasets cleared"}

@router.get('/datasets/{dataset_id}/profile', response_model=ProfileResponse)
def profile(dataset_id: str, current_user: str = Depends(get_current_user)):
    d = get_dataset(dataset_id, owner_id=current_user)
    return profiler.profile(d.id, d.frame)

@router.get('/datasets/{dataset_id}/rows')
def rows(dataset_id: str, offset: int = 0, limit: int = 50, search: str = '', current_user: str = Depends(get_current_user)):
    d = get_dataset(dataset_id, owner_id=current_user)
    frame = d.frame
    if search:
        frame = frame[frame.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)]
    return {
        'rows': frame.iloc[offset:offset+min(limit, 200)].where(frame.notna(), None).to_dict(orient='records'),
        'total': len(frame),
        'columns': d.frame.columns.tolist()
    }

@router.post('/chat', response_model=AnalysisResponse)
@limiter.limit("30/minute")
def chat(
    request: Request,
    body: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    d = get_dataset(body.dataset_id, owner_id=current_user)
    memory.add(body.session_id, 'user', body.message)
    all_data = {registry.table_name(i.id): i.frame for i in registry.list(owner_id=current_user)}
    response = planner.respond_with_context(d.id, all_data, body.message, memory.get(body.session_id))
    memory.add(body.session_id, 'assistant', response.answer)
    return response

@router.post('/generate-sql', response_model=AnalysisResponse)
def sql(request: SqlRequest, current_user: str = Depends(get_current_user)):
    get_dataset(request.dataset_id, owner_id=current_user)
    try:
        user_tables = {registry.table_name(i.id): i.frame for i in registry.list(owner_id=current_user)}
        query, result = sql_tool.run(user_tables, request.query)
        return AnalysisResponse(
            answer=f'Returned {len(result)} rows.',
            reasoning='Executed validated read-only SQL in DuckDB.',
            confidence=.98,
            generated_sql=query,
            metadata={'rows': result, 'tool': 'sql'}
        )
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@router.post('/generate-pandas', response_model=AnalysisResponse)
def pandas(request: PandasRequest, current_user: str = Depends(get_current_user)):
    try:
        result = PandasTool().run(get_dataset(request.dataset_id, owner_id=current_user).frame, request.code)
        return AnalysisResponse(
            answer=f'Returned {len(result)} rows.',
            reasoning='Executed a parsed restricted Pandas expression.',
            confidence=.92,
            generated_pandas=request.code,
            metadata={'rows': result, 'tool': 'pandas'}
        )
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@router.post('/generate-chart', response_model=AnalysisResponse)
def chart(request: ChartRequest, current_user: str = Depends(get_current_user)):
    try:
        return AnalysisResponse(
            answer='Chart generated.',
            reasoning='Validated requested fields and produced a Plotly specification.',
            confidence=.97,
            chart=ChartFactory().create(get_dataset(request.dataset_id, owner_id=current_user).frame, request.chart_type, request.x, request.y),
            metadata={'tool': 'visualization'}
        )
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@router.post('/detect-anomalies', response_model=AnalysisResponse)
def anomalies(dataset_id: str, current_user: str = Depends(get_current_user)):
    items = AnomalyService().detect(get_dataset(dataset_id, owner_id=current_user).frame)
    return AnalysisResponse(
        answer=f'Found {len(items)} potential anomalies.',
        reasoning='Isolation Forest scores numeric outliers.',
        confidence=.82,
        anomalies=items,
        limitations=['Not suitable for categorical-only datasets.'],
        metadata={'tool': 'anomaly'}
    )

@router.post('/detect-anomalies/async', response_model=JobResponse, status_code=202)
def anomalies_async(dataset_id: str, current_user: str = Depends(get_current_user)):
    d = get_dataset(dataset_id, owner_id=current_user)
    frame = d.frame.copy()

    def _task():
        return AnomalyService().detect(frame)

    job_id = job_manager.submit_job("anomaly_detection", current_user, _task)
    return JobResponse(job_id=job_id, job_type="anomaly_detection", status="processing")


