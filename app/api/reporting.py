from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.reporting import DocumentReport, DashboardSummary
from app.services.reporting_service import reporting_service
from app.database import get_db
from typing import List, Dict, Any
from fastapi.responses import FileResponse, Response

from app.models.comparison import ComparisonReport
from app.services.comparison_service import comparison_service

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get high-level summary of all documents and system status.
    """
    return await reporting_service.get_dashboard_summary(db)

@router.get("/compare/{tender_id}", response_model=ComparisonReport)
async def compare_all_bidders(tender_id: str, db: Session = Depends(get_db)):
    """
    Generate a comparison matrix and ranking for all bidders of a specific tender.
    """
    try:
        return await comparison_service.generate_comparison_report(db, tender_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comparison: {str(e)}")

@router.get("/report/{document_id}", response_model=Dict[str, Any])
async def get_document_full_report(document_id: str, db: Session = Depends(get_db)):
    """
    Get full evaluation report including benchmarks, AI verdicts, and human-readable evidence chains.
    """
    try:
        return await reporting_service.get_document_report(db, document_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/report/{document_id}/pdf")
async def get_document_pdf_report(document_id: str, db: Session = Depends(get_db)):
    """
    Download a simple PDF evaluation report.
    """
    try:
        pdf_bytes = await reporting_service.generate_pdf_report(db, document_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=TenderAI_Report_{document_id}.pdf"
            }
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
