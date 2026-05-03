import os
import json
import re
from typing import List, Dict, Any
from app.models.nlp import TenderCriterion
from app.config import settings
from loguru import logger
import google.generativeai as genai
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from app.models.db_models import DBTenderCriterion

class CriteriaExtractionService:
    def __init__(self):
        self.criteria_file = settings.CRITERIA_FILE
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.model = None

    async def extract_criteria(self, db: Session, tender_id: str, full_text: str) -> List[TenderCriterion]:
        """
        3-Pass Criteria Extraction Pipeline with DB Persistence
        """
        # Pass 1: Sectioning
        sections = self._pass1_sectioning(full_text)
        
        # Pass 2: LLM Extraction
        raw_criteria = await self._pass2_llm_extraction(sections)
        
        # Pass 3: Deduplication
        final_criteria = self._pass3_deduplication(raw_criteria)
        
        # Persistence to DB
        self._save_criteria_to_db(db, tender_id, final_criteria)
        
        # Persistence to File (Backup)
        self._save_criteria_to_file(final_criteria)
        
        return final_criteria

    def _save_criteria_to_db(self, db: Session, tender_id: str, criteria: List[TenderCriterion]):
        # Clear existing criteria for this tender
        db.query(DBTenderCriterion).filter(DBTenderCriterion.tender_id == tender_id).delete()
        
        for crit in criteria:
            db_crit = DBTenderCriterion(
                tender_id=tender_id,
                type=crit.type,
                description=crit.description,
                threshold=crit.threshold,
                comparator=crit.comparator
            )
            db.add(db_crit)
        db.commit()

    def _save_criteria_to_file(self, criteria: List[TenderCriterion]):
        os.makedirs(os.path.dirname(self.criteria_file), exist_ok=True)
        with open(self.criteria_file, "w") as f:
            json.dump([c.model_dump() for c in criteria], f, indent=2)

    def _pass1_sectioning(self, text: str) -> List[str]:
        keywords = ["Evaluation Criteria", "Technical Requirements", "Compliance", "Financial Proposal", "Selection Criteria"]
        pattern = "|".join([f"(?i){kw}" for kw in keywords])
        sections = re.split(pattern, text)
        return [s.strip() for s in sections if len(s.strip()) > 50]

    async def _pass2_llm_extraction(self, sections: List[str]) -> List[TenderCriterion]:
        """
        Pass 2: Use LLM (Gemini) to extract criteria into JSON.
        Provides deterministic mock fallback if API key is missing.
        """
        if not self.model:
            logger.warning("Gemini API Key not configured. Using deterministic mock fallback for demo/testing.")
            return [
                TenderCriterion(
                    id="FIN-01", 
                    type="FINANCIAL", 
                    description="Annual turnover must be at least 5 Crore INR.",
                    threshold="50000000",
                    comparator=">="
                ),
                TenderCriterion(
                    id="COMP-01", 
                    type="COMPLIANCE", 
                    description="Bidder must be ISO 27001 certified.",
                    threshold=None,
                    comparator="=="
                )
            ]

        all_criteria = []
        for section in sections:
            prompt = f"""
            Extract tender evaluation criteria from the following text into a JSON list.
            Each criterion must have:
            - id: Unique short string (e.g., TECH-01)
            - type: One of [FINANCIAL, TECHNICAL, COMPLIANCE]
            - description: Detailed description of the requirement
            - threshold: Any specific numerical threshold if mentioned (else null)
            - comparator: Comparison operator if mentioned (e.g., >=, <=, ==) (else null)

            Text:
            {section[:2000]}
            
            Return ONLY the JSON list.
            """
            try:
                response = self.model.generate_content(prompt)
                json_str = self._extract_json_from_text(response.text)
                if json_str:
                    items = json.loads(json_str)
                    for item in items:
                        all_criteria.append(TenderCriterion(**item))
            except Exception as e:
                logger.error(f"Gemini extraction failed for a section: {str(e)}")
        
        return all_criteria

    def _pass3_deduplication(self, criteria: List[TenderCriterion]) -> List[TenderCriterion]:
        if not criteria: return []
        unique_criteria = []
        for crit in criteria:
            is_duplicate = False
            for existing in unique_criteria:
                similarity = SequenceMatcher(None, crit.description.lower(), existing.description.lower()).ratio()
                if similarity > 0.85:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_criteria.append(crit)
        return unique_criteria

    def _extract_json_from_text(self, text: str) -> str:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        return match.group(0) if match else None

criteria_extraction_service = CriteriaExtractionService()
