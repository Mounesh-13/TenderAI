import os
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.reporting import DocumentReport, DashboardSummary
from app.models.db_models import DBDocument, DBHITLReview, DBTenderCriterion
from app.models.evaluation import EvaluationResult
from app.models.explainability import DocumentEvidenceChain
from app.config import settings
from fpdf import FPDF
from datetime import datetime
from loguru import logger

class ReportingService:
    def __init__(self):
        self.eval_dir = settings.EVALUATION_DIR
        self.evidence_chain_file = "data/evidence_chain.json"

    async def get_document_report(self, db: Session, document_id: str) -> Dict[str, Any]:
        """
        Generates the final report: Combines criteria, verdicts, and evidence chains.
        """
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not db_doc:
            raise FileNotFoundError(f"Document {document_id} not found.")

        db_criteria = db.query(DBTenderCriterion).filter(DBTenderCriterion.tender_id == db_doc.parent_tender_id).all()
        criteria_list = [
            {"id": c.id, "type": c.type, "description": c.description, "threshold": c.threshold}
            for c in db_criteria
        ]

        eval_path = os.path.join(self.eval_dir, f"{document_id}.json")
        evaluation = None
        if os.path.exists(eval_path):
            with open(eval_path, "r") as f:
                evaluation = json.load(f)

        evidence_chain = self._get_chain_from_file(document_id)

        hitl_review = db.query(DBHITLReview).filter(DBHITLReview.document_id == document_id).first()
        hitl_data = None
        if hitl_review:
            hitl_data = {
                "decision": hitl_review.decision,
                "reason": hitl_review.reason,
                "reviewer_id": hitl_review.reviewer_id,
                "reviewed_at": hitl_review.reviewed_at.isoformat()
            }

        return {
            "report_metadata": {
                "document_id": document_id,
                "filename": db_doc.filename,
                "status": db_doc.status,
                "overall_score": db_doc.final_verdict if db_doc.status == "completed" else (evaluation.get("overall_score") if evaluation else 0.0),
                "generated_at": datetime.utcnow().isoformat()
            },
            "tender_benchmarks": criteria_list,
            "ai_evaluation": evaluation,
            "evidence_chains": [c.model_dump() for c in evidence_chain.chains] if evidence_chain else [],
            "expert_review": hitl_data
        }

    def _clean_text(self, text: Any) -> str:
        """Force text into Latin-1, replacing any incompatible characters with '?'."""
        if text is None: return ""
        s = str(text).replace("→", "->").replace("—", "-").replace("–", "-")
        return s.encode('latin-1', 'replace').decode('latin-1')

    async def generate_pdf_report(self, db: Session, document_id: str) -> bytes:
        """
        Generates a PDF report using the most basic, failsafe method.
        """
        try:
            data = await self.get_document_report(db, document_id)
            pdf = FPDF()
            pdf.add_page()
            
            # TITLE
            pdf.set_font("helvetica", 'B', 16)
            pdf.write(10, "TenderAI Evaluation Report\n\n")
            
            # INFO
            pdf.set_font("helvetica", size=12)
            pdf.write(8, self._clean_text(f"Document ID: {document_id}\n"))
            pdf.write(8, self._clean_text(f"Filename: {data['report_metadata']['filename']}\n"))
            score = data['report_metadata']['overall_score'] * 100
            pdf.write(8, f"Overall Score: {score:.1f}%\n\n")

            # EVIDENCE
            pdf.set_font("helvetica", 'B', 14)
            pdf.write(10, "AI Evidence Chains\n")
            pdf.set_font("helvetica", size=10)
            
            if not data["evidence_chains"]:
                pdf.write(8, "No evidence chains found.\n")
            else:
                for chain in data["evidence_chains"]:
                    pdf.write(7, self._clean_text(f"- {chain['summary']}\n"))
            
            return bytes(pdf.output())
        except Exception as e:
            logger.error(f"FINAL PDF ERROR: {str(e)}")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=12)
            pdf.write(10, f"Error generating report: {str(e)}")
            return bytes(pdf.output())

    async def get_dashboard_summary(self, db: Session) -> DashboardSummary:
        total = db.query(DBDocument).count()
        processed = db.query(DBDocument).filter(DBDocument.status == "processed").count()
        completed = db.query(DBDocument).filter(DBDocument.status == "completed").count()
        recent_docs = db.query(DBDocument).order_by(DBDocument.upload_timestamp.desc()).limit(5).all()
        recent_reports = [{"id": d.id, "filename": d.filename, "status": d.status, "date": d.upload_timestamp.isoformat(), "verdict": d.final_verdict} for d in recent_docs]
        return DashboardSummary(total_documents=total, processed_count=processed + completed, pending_review=processed, recent_reports=recent_reports)

    def _get_chain_from_file(self, document_id: str) -> Optional[DocumentEvidenceChain]:
        if not os.path.exists(self.evidence_chain_file): return None
        with open(self.evidence_chain_file, "r") as f:
            all_chains = json.load(f)
            for item in all_chains:
                if item["document_id"] == document_id: return DocumentEvidenceChain(**item)
        return None

reporting_service = ReportingService()
