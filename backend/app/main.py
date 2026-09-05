import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.config import settings
from app.database.connection import Base, engine
import app.database.models  # ensure models are registered with Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version='1.0.0')

origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
is_wildcard = '*' in origins or not origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if is_wildcard else origins,
    allow_credentials=not is_wildcard,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
app.include_router(router, prefix='/api')

@app.get('/health')
def health():
    return {'status': 'ok'}

