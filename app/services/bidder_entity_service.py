import os
import json
import re
from typing import List, Dict, Any
from app.config import settings
from loguru import logger
import spacy

class BidderEntityService:
    def __init__(self):
        self.evidence_file = "data/evidence.json"
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning("spaCy model 'en_core_web_sm' not found. Bidder extraction will rely on regex.")
            self.nlp = None

    async def extract_and_normalize(self, text: str, document_id: str) -> Dict[str, Any]:
        """
        Extracts entities (Money, Dates, Orgs) and normalizes money to INR.
        """
        entities = {
            "document_id": document_id,
            "organizations": [],
            "dates": [],
            "money": [],
            "raw_money_values": []
        }

        # 1. spaCy extraction for Orgs and Dates
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    entities["organizations"].append(ent.text.strip())
                elif ent.label_ == "DATE":
                    entities["dates"].append(ent.text.strip())
                elif ent.label_ == "MONEY":
                    entities["raw_money_values"].append(ent.text.strip())

        # 2. Regex for Money extraction and normalization
        entities["money"] = self._extract_and_normalize_money(text)

        # Deduplicate orgs and dates
        entities["organizations"] = list(set(entities["organizations"]))
        entities["dates"] = list(set(entities["dates"]))

        # Persistence
        self._save_evidence(entities)

        return entities

    def _extract_and_normalize_money(self, text: str) -> List[int]:
        """
        Regex-based money extraction and normalization to INR.
        Handles: ₹, Rs, INR, Lakh, Crore, K, M
        """
        # Pattern to find money-like strings
        # Supports: 1,00,000, 10.5 Lakh, 2 Crore, Rs. 500, etc.
        money_pattern = r"(?:(?:Rs|INR|₹)\.?\s?)?(\d+(?:,\d+)*(?:\.\d+)?)\s?(Lakh|Crore|Cr|L|K|M|million|billion)?"
        matches = re.finditer(money_pattern, text, re.IGNORECASE)
        
        normalized_values = []
        for match in matches:
            try:
                value_str = match.group(1).replace(",", "")
                value = float(value_str)
                suffix = match.group(2)
                
                if suffix:
                    suffix = suffix.lower()
                    if suffix in ["lakh", "l"]:
                        value *= 100_000
                    elif suffix in ["crore", "cr"]:
                        value *= 10_000_000
                    elif suffix == "k":
                        value *= 1_000
                    elif suffix in ["m", "million"]:
                        value *= 1_000_000
                    elif suffix == "billion":
                        value *= 1_000_000_000
                
                normalized_values.append(int(value))
            except Exception:
                continue
        
        return list(set(normalized_values))

    def _save_evidence(self, entities: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.evidence_file), exist_ok=True)
        
        # Load existing if any and append/update
        evidence_data = []
        if os.path.exists(self.evidence_file):
            try:
                with open(self.evidence_file, "r") as f:
                    evidence_data = json.load(f)
            except Exception:
                evidence_data = []

        # Update or append
        updated = False
        for i, item in enumerate(evidence_data):
            if item["document_id"] == entities["document_id"]:
                evidence_data[i] = entities
                updated = True
                break
        
        if not updated:
            evidence_data.append(entities)

        with open(self.evidence_file, "w") as f:
            json.dump(evidence_data, f, indent=2)

bidder_entity_service = BidderEntityService()
