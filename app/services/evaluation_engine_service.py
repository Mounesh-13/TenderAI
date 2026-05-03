import os
import json
from typing import List, Dict, Any
from app.models.evaluation import EvaluationResult, CriterionScore, Evidence
from app.models.nlp import TenderCriterion
from app.config import settings
from datetime import datetime
from loguru import logger

from app.services.explainability_service import explainability_service

from app.models.db_models import DBDocument, DBTenderCriterion

class EvaluationEngineService:
    def __init__(self):
        self.criteria_file = settings.CRITERIA_FILE
        self.evidence_file = "data/evidence.json"
        self.eval_dir = settings.EVALUATION_DIR
        if not os.path.exists(self.eval_dir):
            os.makedirs(self.eval_dir)

    async def evaluate_bidder(self, db: Session, document_id: str) -> EvaluationResult:
        """
        Matches bidder evidence against tender criteria loaded from DB.
        """
        # 1. Get Bidder Doc to find Parent Tender
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not db_doc or not db_doc.parent_tender_id:
            raise ValueError(f"Document {document_id} is not a valid bidder document linked to a tender.")

        # 2. Load Criteria for the parent tender
        criteria = self._load_criteria_from_db(db, db_doc.parent_tender_id)
        if not criteria:
            # Fallback to file-based for backward compatibility during migration
            criteria = self._load_criteria()
        
        # 3. Load Bidder Evidence
        bidder_evidence = self._load_bidder_evidence(document_id)
        if not bidder_evidence:
            raise FileNotFoundError(f"No evidence found for document {document_id}")

        # 4. Evaluate each criterion
        criteria_scores = []
        for crit in criteria:
            score_entry = self._evaluate_single_criterion(crit, bidder_evidence)
            criteria_scores.append(score_entry)

        # 5. Calculate Overall Score
        overall_score = 0.0
        if criteria_scores:
            eligible_count = sum(1 for s in criteria_scores if s.status == "ELIGIBLE")
            overall_score = eligible_count / len(criteria_scores)

        result = EvaluationResult(
            document_id=document_id,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            evaluator_engine="TenderAI-EvalEngine-v2",
            evaluated_at=datetime.utcnow()
        )

        # 6. Generate Explainability Evidence Chain
        await explainability_service.generate_chain(document_id, criteria, result)

        # Save result
        output_path = os.path.join(self.eval_dir, f"{document_id}.json")
        with open(output_path, "w") as f:
            f.write(result.model_dump_json())

        return result

    def _load_criteria_from_db(self, db: Session, tender_id: str) -> List[TenderCriterion]:
        db_criteria = db.query(DBTenderCriterion).filter(DBTenderCriterion.tender_id == tender_id).all()
        return [
            TenderCriterion(
                id=c.id,
                type=c.type,
                description=c.description,
                threshold=c.threshold,
                comparator=c.comparator
            ) for c in db_criteria
        ]

    def _evaluate_single_criterion(self, crit: TenderCriterion, evidence: Dict[str, Any]) -> CriterionScore:
        """
        Logic for matching and scoring. Enforces 0.85 confidence threshold for HITL.
        """
        verdict = "REVIEW"
        extracted_value = "N/A"
        confidence = 0.5
        reasoning = "Automatic match unclear."
        evidences = []

        if crit.type == "FINANCIAL":
            verdict, extracted_value, confidence, reasoning = self._match_financial(crit, evidence)
        elif crit.type == "COMPLIANCE":
            verdict, extracted_value, confidence, reasoning = self._match_compliance(crit, evidence)
        else:
            reasoning = f"Criterion type {crit.type} requires manual review."

        # HITL Requirement: If confidence < 0.85 → mark as REVIEW
        if confidence < 0.85:
            verdict = "REVIEW"
            reasoning = f"Low confidence ({confidence}). Requires manual review. original reasoning: {reasoning}"

        # Wrap as Evidence objects for the model
        evidences.append(Evidence(
            requirement_id=crit.id,
            text_snippet=str(extracted_value),
            page_number=1,
            confidence_score=confidence
        ))

        return CriterionScore(
            requirement_id=crit.id,
            score=1.0 if verdict == "ELIGIBLE" else (0.0 if verdict == "NOT_ELIGIBLE" else 0.5),
            status=verdict,
            reasoning=reasoning,
            evidence=evidences
        )

    def _match_financial(self, crit: TenderCriterion, evidence: Dict[str, Any]) -> tuple:
        """
        Financial rule: correctly uses the criterion's comparator (>=, <=, ==, >, <).
        """
        threshold_val = self._parse_numeric(crit.threshold)
        if threshold_val is None:
            return "REVIEW", "N/A", 0.3, "Could not parse threshold value from criterion."

        # Find best match in normalized money evidence
        money_values = evidence.get("money", [])
        if not money_values:
            return "NOT_ELIGIBLE", "0", 0.8, "No financial figures found in document."

        # Define comparator logic
        operators = {
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b
        }
        comp_func = operators.get(crit.comparator, lambda a, b: a >= b)
        
        met_threshold = [v for v in money_values if comp_func(v, threshold_val)]
        
        if met_threshold:
            # If multiple values meet criteria, pick the "best" one (usually largest for >=, smallest for <=)
            best_val = max(met_threshold) if crit.comparator != "<=" and crit.comparator != "<" else min(met_threshold)
            return "ELIGIBLE", f"INR {best_val:,}", 0.9, f"Extracted value {best_val:,} satisfies {crit.comparator or '>='} {threshold_val:,}."
        else:
            best_val = max(money_values)
            return "NOT_ELIGIBLE", f"INR {best_val:,}", 0.9, f"Highest extracted value {best_val:,} does not satisfy {crit.comparator or '>='} {threshold_val:,}."

    def _match_compliance(self, crit: TenderCriterion, evidence: Dict[str, Any]) -> tuple:
        """
        Document presence / Organization match.
        """
        desc_lower = crit.description.lower()
        
        # Check organizations
        for org in evidence.get("organizations", []):
            if org.lower() in desc_lower or desc_lower in org.lower():
                return "ELIGIBLE", org, 0.7, f"Organization '{org}' identified in relation to compliance requirement."

        # Generic keyword match in evidence? 
        # (This is a simplification)
        return "REVIEW", "N/A", 0.4, "Could not automatically verify compliance."

    def _parse_numeric(self, val_str: str) -> float:
        if not val_str: return None
        try:
            # Clean string and convert to float
            # Assumes the normalization already happened if it came from our extractor
            clean_val = re.sub(r"[^\d.]", "", val_str)
            return float(clean_val)
        except Exception:
            return None

    def _load_criteria(self) -> List[TenderCriterion]:
        if not os.path.exists(self.criteria_file):
            return []
        with open(self.criteria_file, "r") as f:
            data = json.load(f)
            return [TenderCriterion(**item) for item in data]

    def _load_bidder_evidence(self, document_id: str) -> Dict[str, Any]:
        if not os.path.exists(self.evidence_file):
            return None
        with open(self.evidence_file, "r") as f:
            data = json.load(f)
            for item in data:
                if item["document_id"] == document_id:
                    return item
        return None

import re
evaluation_engine_service = EvaluationEngineService()
