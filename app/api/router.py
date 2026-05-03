from fastapi import APIRouter, Depends
from app.api import ingestion, ocr, nlp, evaluation, hitl, audit, pipelines, reporting, auth
from app.api.auth import get_current_user

api_router = APIRouter()

# Public routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Protected routes
api_router.include_router(
    ingestion.router, 
    prefix="/ingestion", 
    tags=["ingestion"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    ocr.router, 
    prefix="/ocr", 
    tags=["ocr"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    nlp.router, 
    prefix="/nlp", 
    tags=["nlp"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    evaluation.router, 
    prefix="/evaluation", 
    tags=["evaluation"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    hitl.router, 
    prefix="/hitl", 
    tags=["hitl"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    audit.router, 
    prefix="/audit", 
    tags=["audit"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    pipelines.router, 
    prefix="/pipelines", 
    tags=["pipelines"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    reporting.router, 
    prefix="/reporting", 
    tags=["reporting"],
    dependencies=[Depends(get_current_user)]
)

# Placeholder for future routes
@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}
