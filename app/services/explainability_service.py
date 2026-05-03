import os
import json
from typing import List, Dict, Any
from app.models.explainability import EvidenceChainItem, DocumentEvidenceChain
from app.models.evaluation import EvaluationResult, CriterionScore
from app.models.nlp import TenderCriterion
from datetime import datetime
from loguru import logger
from app.config import settings

class ExplainabilityService:
    def __init__(self, output_file: str = "data/evidence_chain.json"):
        self.output_file = output_file
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

    async def generate_chain(self, document_id: str, criteria: List[TenderCriterion], eval_result: EvaluationResult) -> DocumentEvidenceChain:
        """
        Generates a human-readable evidence chain for a document's evaluation.
        """
        chains = []
        criteria_map = {c.id: c for c in criteria}

        for score in eval_result.criteria_scores:
            crit = criteria_map.get(score.requirement_id)
            if not crit:
                continue

            # Extract info from score and evidence
            verdict_map = {"ELIGIBLE": "PASS", "NOT_ELIGIBLE": "FAIL", "REVIEW": "REVIEW"}
            comparison_result = verdict_map.get(score.status, "REVIEW")
            
            # Use the first evidence piece for the chain
            evidence_item = score.evidence[0] if score.evidence else None
            extracted_value = evidence_item.text_snippet if evidence_item else "N/A"
            source_page = evidence_item.page_number if evidence_item else 0

            # Generate Human-Readable Summary
            # Format: "Criterion → Extracted Value (Page X) → RESULT"
            criterion_display = f"{crit.description}"
            if crit.threshold and crit.comparator:
                # Handle potential symbol conversion for cleaner display
                display_comp = crit.comparator.replace(">=", "≥").replace("<=", "≤")
                criterion_display = f"{crit.description} ({display_comp} {crit.threshold})"
            
            summary = f"{criterion_display} → Extracted: {extracted_value} (Page {source_page}) → {comparison_result}"

            chains.append(EvidenceChainItem(
                criterion_id=crit.id,
                criterion_text=crit.description,
                extracted_value=extracted_value,
                comparison_result=comparison_result,
                source_page=source_page,
                summary=summary
            ))

        chain_result = DocumentEvidenceChain(
            document_id=document_id,
            chains=chains,
            generated_at=datetime.utcnow()
        )

        # Persistence
        self._save_chain(chain_result)

        return chain_result

    def _save_chain(self, chain: DocumentEvidenceChain):
        all_chains = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r") as f:
                    all_chains = json.load(f)
            except Exception:
                all_chains = []

        # Update or append
        updated = False
        for i, item in enumerate(all_chains):
            if item["document_id"] == chain.document_id:
                all_chains[i] = chain.model_dump(mode='json')
                updated = True
                break
        
        if not updated:
            all_chains.append(chain.model_dump(mode='json'))

        with open(self.output_file, "w") as f:
            json.dump(all_chains, f, indent=2)

explainability_service = ExplainabilityService()
