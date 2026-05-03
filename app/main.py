from fastapi import FastAPI
from app.api.router import api_router
from app.database import engine, Base
from app.models import db_models
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI system for tender evaluation",
    version=settings.VERSION,
)

@app.get("/")
async def root():
    return {"message": "Welcome to TenderAI API", "status": "running"}

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
