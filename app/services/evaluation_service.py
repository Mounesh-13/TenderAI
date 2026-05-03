import os
import json
from app.models.evaluation import EvaluationResult, CriterionScore, Evidence
from app.models.nlp import NLPAnalysisResult
from app.models.ocr import OCRResult
from datetime import datetime
import asyncio
from app.config import settings

class EvaluationService:
    def __init__(self, nlp_dir: str = settings.NLP_DIR, ocr_dir: str = settings.OCR_DIR, eval_dir: str = settings.EVALUATION_DIR):
        self.nlp_dir = nlp_dir
        self.ocr_dir = ocr_dir
        self.eval_dir = eval_dir
        if not os.path.exists(self.eval_dir):
            os.makedirs(self.eval_dir)

    async def evaluate_document(self, document_id: str) -> EvaluationResult:
        # Load NLP Result
        nlp_path = os.path.join(self.nlp_dir, f"{document_id}.json")
        if not os.path.exists(nlp_path):
            raise FileNotFoundError(f"NLP analysis for document {document_id} not found.")

        with open(nlp_path, "r") as f:
            nlp_data = json.load(f)
            nlp_result = NLPAnalysisResult(**nlp_data)

        # Simulate Evaluation delay
        await asyncio.sleep(2)

        criteria_scores = []
        for req in nlp_result.requirements:
            status = "Compliant"
            score = 0.95
            evidence = [
                Evidence(
                    requirement_id=req.id,
                    text_snippet=f"Found match for {req.description}",
                    page_number=1,
                    confidence_score=0.9
                )
            ]

            criteria_scores.append(CriterionScore(
                requirement_id=req.id,
                score=score,
                status=status,
                reasoning=f"Requirement {req.id} satisfied.",
                evidence=evidence
            ))

        overall_score = sum([c.score for c in criteria_scores]) / len(criteria_scores) if criteria_scores else 0.0

        result = EvaluationResult(
            document_id=document_id,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            evaluator_engine=f"TenderAI-{settings.LLM_PROVIDER}-v1",
            evaluated_at=datetime.now()
        )

        output_path = os.path.join(self.eval_dir, f"{document_id}.json")
        with open(output_path, "w") as f:
            f.write(result.model_dump_json())

        return result

evaluation_service = EvaluationService()
