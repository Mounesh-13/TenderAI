from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.pipelines.tender_pipeline import tender_pipeline
from app.database import get_db

router = APIRouter()

@router.post("/process/{document_id}")
async def trigger_full_pipeline(
    document_id: str, 
    background_tasks: BackgroundTasks, 
    run_sync: bool = False,
    db: Session = Depends(get_db)
):
    """
    Trigger the appropriate pipeline based on document type.
    Support run_sync=True for immediate execution (demo safety).
    """
    db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        if db_doc.doc_type == "tender":
            if run_sync:
                await tender_pipeline.run_tender_pipeline(db, document_id)
            else:
                background_tasks.add_task(tender_pipeline.run_tender_pipeline, db, document_id)
            return {"message": "Tender Pipeline processed", "document_id": document_id, "sync": run_sync}
        else:
            if not db_doc.parent_tender_id:
                raise HTTPException(status_code=400, detail="Bidder document must have a parent_tender_id to be evaluated.")
            
            if run_sync:
                await tender_pipeline.run_bidder_pipeline(db, document_id)
            else:
                background_tasks.add_task(tender_pipeline.run_bidder_pipeline, db, document_id)
            return {"message": "Bidder Pipeline processed", "document_id": document_id, "sync": run_sync}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger pipeline: {str(e)}")
