import os
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.comparison import ComparisonReport, BidderComparisonItem
from app.models.db_models import DBDocument, DBTenderCriterion
from app.models.evaluation import EvaluationResult
from app.config import settings
from datetime import datetime

class ComparisonService:
    def __init__(self):
        self.eval_dir = settings.EVALUATION_DIR

    async def generate_comparison_report(self, db: Session, tender_id: str) -> ComparisonReport:
        # 1. Get Tender Info
        tender_doc = db.query(DBDocument).filter(DBDocument.id == tender_id).first()
        if not tender_doc:
            raise FileNotFoundError(f"Tender {tender_id} not found.")

        # 2. Get all Bidders for this Tender
        bidders = db.query(DBDocument).filter(
            DBDocument.parent_tender_id == tender_id,
            DBDocument.doc_type == "bidder"
        ).all()

        bidder_items = []
        for bidder in bidders:
            # Load evaluation result from file
            eval_path = os.path.join(self.eval_dir, f"{bidder.id}.json")
            if not os.path.exists(eval_path):
                continue
            
            with open(eval_path, "r") as f:
                eval_data = EvaluationResult(**json.load(f))

            # Map criteria scores to breakdown
            breakdown = {s.requirement_id: s.score for s in eval_data.criteria_scores}

            bidder_items.append(BidderComparisonItem(
                document_id=bidder.id,
                filename=bidder.filename,
                overall_score=eval_data.overall_score,
                status=bidder.status,
                verdict=bidder.final_verdict,
                criteria_breakdown=breakdown
            ))

        # 3. Sort by score for ranking
        sorted_bidders = sorted(bidder_items, key=lambda x: x.overall_score, reverse=True)
        ranking = [b.document_id for b in sorted_bidders]

        return ComparisonReport(
            tender_id=tender_id,
            tender_filename=tender_doc.filename,
            generated_at=datetime.utcnow(),
            bidders=bidder_items,
            ranking=ranking
        )

comparison_service = ComparisonService()
