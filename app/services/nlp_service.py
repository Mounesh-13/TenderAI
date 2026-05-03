import os
import json
import asyncio
from datetime import datetime
from typing import List, Tuple

from app.models.nlp import NLPAnalysisResult, Entity, Requirement
from app.models.ocr import OCRResult
from app.config import settings
from loguru import logger

# NLP Libraries
import spacy
from spacy.matcher import Matcher

class NLPService:
    def __init__(self, ocr_dir: str = settings.OCR_DIR, nlp_dir: str = settings.NLP_DIR):
        self.ocr_dir = ocr_dir
        self.nlp_dir = nlp_dir
        if not os.path.exists(self.nlp_dir):
            os.makedirs(self.nlp_dir)
        
        # Load spaCy model (English)
        # Note: In a real environment, you'd run 'python -m spacy download en_core_web_sm'
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning("spaCy model 'en_core_web_sm' not found. NLP extraction will be limited. Run 'python -m spacy download en_core_web_sm'.")
            self.nlp = None

    async def analyze_document(self, document_id: str) -> NLPAnalysisResult:
        """
        Performs semantic analysis and requirement extraction on the OCR text.
        """
        # 1. Load OCR Result
        ocr_path = os.path.join(self.ocr_dir, f"{document_id}.json")
        if not os.path.exists(ocr_path):
            raise FileNotFoundError(f"OCR result for document {document_id} not found.")

        with open(ocr_path, "r") as f:
            ocr_data = json.load(f)
            ocr_result = OCRResult(**ocr_data)

        full_text = " ".join([page.text for page in ocr_result.pages])

        if not self.nlp:
            return self._mock_analysis(document_id, "NLP model missing. Using mock.")

        # 2. Process Text with spaCy
        doc = self.nlp(full_text)

        # 3. Extract Entities
        entities = []
        for ent in doc.ents:
            entities.append(Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char
            ))

        # 4. Extract Requirements using Pattern Matching
        requirements = self._extract_requirements(doc)

        # 5. Generate Basic Summary
        summary = self._generate_summary(doc)

        result = NLPAnalysisResult(
            document_id=document_id,
            entities=entities,
            requirements=requirements,
            summary=summary,
            analyzed_at=datetime.utcnow()
        )

        # Save result to data/nlp for persistence
        output_path = os.path.join(self.nlp_dir, f"{document_id}.json")
        with open(output_path, "w") as f:
            f.write(result.model_dump_json())

        return result

    def _extract_requirements(self, doc) -> List[Requirement]:
        """
        Identifies requirements based on modal verbs and imperative language.
        """
        requirements = []
        requirement_keywords = ["must", "shall", "required", "mandatory", "will", "should"]
        
        req_id_counter = 1
        for sent in doc.sents:
            text_lower = sent.text.lower()
            if any(keyword in text_lower for keyword in requirement_keywords):
                # Classify priority
                priority = "Mandatory" if any(k in text_lower for k in ["must", "shall", "mandatory"]) else "Desirable"
                
                # Classify category (Heuristic)
                category = "Technical"
                if any(k in text_lower for k in ["price", "cost", "fee", "payment"]):
                    category = "Financial"
                elif any(k in text_lower for k in ["legal", "contract", "liability", "compliance"]):
                    category = "Legal"

                requirements.append(Requirement(
                    id=f"REQ-{req_id_counter:03d}",
                    description=sent.text.strip(),
                    priority=priority,
                    category=category
                ))
                req_id_counter += 1
        
        return requirements

    def _generate_summary(self, doc) -> str:
        """
        Simple summary: Take the first few sentences or key sentences.
        """
        sentences = list(doc.sents)
        if not sentences:
            return "No text available for summary."
        
        # Take first 3 sentences as a basic summary
        summary_text = " ".join([s.text.strip() for s in sentences[:3]])
        return f"{summary_text}..."

    def _mock_analysis(self, document_id: str, note: str) -> NLPAnalysisResult:
        return NLPAnalysisResult(
            document_id=document_id,
            entities=[],
            requirements=[Requirement(id="MOCK-001", description=f"Note: {note}", priority="High", category="System")],
            summary=note,
            analyzed_at=datetime.utcnow()
        )

nlp_service = NLPService()
