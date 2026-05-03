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

    async def generate_pdf_report(self, db: Session, document_id: str) -> str:
        """
        Generates a simple PDF report and returns the file path.
        """
        data = await self.get_document_report(db, document_id)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="TenderAI Evaluation Report", ln=True, align='C')
        
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Document ID: {document_id}", ln=True)
        pdf.cell(200, 10, txt=f"Filename: {data['report_metadata']['filename']}", ln=True)
        pdf.cell(200, 10, txt=f"Status: {data['report_metadata']['status']}", ln=True)
        
        # Benchmarks
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Tender Benchmarks:", ln=True)
        pdf.set_font("Arial", size=10)
        for crit in data["tender_benchmarks"]:
            pdf.multi_cell(0, 10, txt=f"- [{crit['id']}] {crit['type']}: {crit['description']}")

        # Evidence Chains
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Evidence Chains:", ln=True)
        pdf.set_font("Arial", size=10)
        for chain in data["evidence_chains"]:
            pdf.multi_cell(0, 10, txt=f"{chain['summary']}")

        # Expert Review
        if data["expert_review"]:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Expert Decision:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt=f"Verdict: {data['expert_review']['decision']}", ln=True)
            pdf.multi_cell(0, 10, txt=f"Reason: {data['expert_review']['reason']}")

        report_dir = "data/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"{document_id}.pdf")
        pdf.output(report_path)
        
        return report_path

    async def get_dashboard_summary(self, db: Session) -> DashboardSummary:
        total = db.query(DBDocument).count()
        processed = db.query(DBDocument).filter(DBDocument.status == "processed").count()
        completed = db.query(DBDocument).filter(DBDocument.status == "completed").count()
        
        recent_docs = db.query(DBDocument).order_by(DBDocument.upload_timestamp.desc()).limit(5).all()
        recent_reports = [
            {"id": d.id, "filename": d.filename, "status": d.status, "date": d.upload_timestamp.isoformat(), "verdict": d.final_verdict}
            for d in recent_docs
        ]

        return DashboardSummary(
            total_documents=total,
            processed_count=processed + completed,
            pending_review=processed,
            recent_reports=recent_reports
        )

    def _get_chain_from_file(self, document_id: str) -> Optional[DocumentEvidenceChain]:
        if not os.path.exists(self.evidence_chain_file):
            return None
        
        with open(self.evidence_chain_file, "r") as f:
            all_chains = json.load(f)
            for item in all_chains:
                if item["document_id"] == document_id:
                    return DocumentEvidenceChain(**item)
        return None

reporting_service = ReportingService()
