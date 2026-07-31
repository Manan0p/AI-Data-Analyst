import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
app=FastAPI(title=settings.app_name,version='1.0.0');app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins.split(','),allow_credentials=True,allow_methods=['*'],allow_headers=['*']);app.include_router(router,prefix='/api')
@app.get('/health')
def health():return {'status':'ok'}
