import logging
from fastapi import APIRouter,File,HTTPException,UploadFile
from app.agents.planner import GeminiPlannerAgent
from app.analytics.anomalies import AnomalyService
from app.analytics.profiler import ProfileService
from app.charts.factory import ChartFactory
from app.database.registry import registry
from app.memory.session import memory
from app.schemas.contracts import *
from app.services.ingestion import CsvIngestionService
from app.tools.pandas_tool import PandasTool
from app.tools.sql_tool import sql_tool
router=APIRouter();ingestion=CsvIngestionService(registry);profiler=ProfileService();planner=GeminiPlannerAgent();logger=logging.getLogger(__name__)
def get_dataset(dataset_id):
    try:return registry.get(dataset_id)
    except KeyError as exc:raise HTTPException(404,str(exc)) from exc
def summary(d):return DatasetSummary(id=d.id,name=d.name,rows=len(d.frame),columns=len(d.frame.columns),preview=d.frame.head(10).where(d.frame.notna(),None).to_dict(orient='records'))
@router.post('/upload',response_model=list[DatasetSummary])
async def upload(files:list[UploadFile]=File(...)):return [summary(await ingestion.ingest(f)) for f in files]
@router.get('/datasets',response_model=list[DatasetSummary])
def datasets():return [summary(d) for d in registry.list()]
@router.get('/datasets/{dataset_id}/profile',response_model=ProfileResponse)
def profile(dataset_id:str):d=get_dataset(dataset_id);return profiler.profile(d.id,d.frame)
@router.get('/datasets/{dataset_id}/rows')
def rows(dataset_id:str,offset:int=0,limit:int=50,search:str=''):
    d=get_dataset(dataset_id);frame=d.frame
    if search:frame=frame[frame.astype(str).apply(lambda c:c.str.contains(search,case=False,na=False)).any(axis=1)]
    return {'rows':frame.iloc[offset:offset+min(limit,200)].where(frame.notna(),None).to_dict(orient='records'),'total':len(frame),'columns':d.frame.columns.tolist()}
@router.post('/chat',response_model=AnalysisResponse)
def chat(request:ChatRequest):
    d=get_dataset(request.dataset_id);memory.add(request.session_id,'user',request.message);all_data={registry.table_name(i.id):i.frame for i in registry.list()};response=planner.respond_with_context(d.id,all_data,request.message,memory.get(request.session_id));memory.add(request.session_id,'assistant',response.answer);return response
@router.post('/generate-sql',response_model=AnalysisResponse)
def sql(request:SqlRequest):
    get_dataset(request.dataset_id)
    try:query,result=sql_tool.run({registry.table_name(i.id):i.frame for i in registry.list()},request.query);return AnalysisResponse(answer=f'Returned {len(result)} rows.',reasoning='Executed validated read-only SQL in DuckDB.',confidence=.98,generated_sql=query,metadata={'rows':result,'tool':'sql'})
    except Exception as exc:raise HTTPException(400,str(exc)) from exc
@router.post('/generate-pandas',response_model=AnalysisResponse)
def pandas(request:PandasRequest):
    try:result=PandasTool().run(get_dataset(request.dataset_id).frame,request.code);return AnalysisResponse(answer=f'Returned {len(result)} rows.',reasoning='Executed a parsed restricted Pandas expression.',confidence=.92,generated_pandas=request.code,metadata={'rows':result,'tool':'pandas'})
    except Exception as exc:raise HTTPException(400,str(exc)) from exc
@router.post('/generate-chart',response_model=AnalysisResponse)
def chart(request:ChartRequest):
    try:return AnalysisResponse(answer='Chart generated.',reasoning='Validated requested fields and produced a Plotly specification.',confidence=.97,chart=ChartFactory().create(get_dataset(request.dataset_id).frame,request.chart_type,request.x,request.y),metadata={'tool':'visualization'})
    except Exception as exc:raise HTTPException(400,str(exc)) from exc
@router.post('/detect-anomalies',response_model=AnalysisResponse)
def anomalies(dataset_id:str):items=AnomalyService().detect(get_dataset(dataset_id).frame);return AnalysisResponse(answer=f'Found {len(items)} potential anomalies.',reasoning='Isolation Forest scores numeric outliers.',confidence=.82,anomalies=items,limitations=['Not suitable for categorical-only datasets.'],metadata={'tool':'anomaly'})
