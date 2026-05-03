from sqlalchemy.orm import Session
from app.services.ocr_service import ocr_service
from app.services.bidder_entity_service import bidder_entity_service
from app.services.evaluation_engine_service import evaluation_engine_service
from app.services.audit_service import audit_service
from app.models.db_models import DBDocument
from loguru import logger

from app.services.criteria_extraction_service import criteria_extraction_service

class TenderPipeline:
    async def run_tender_pipeline(self, db: Session, document_id: str):
        """
        Orchestrates: OCR -> Criteria Extraction (Rules)
        """
        logger.info(f"📋 Starting Tender Pipeline (Rules Extraction) for: {document_id}")
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        try:
            # 1. OCR Layer
            ocr_result = await ocr_service.process_document(db, document_id)
            full_text = " ".join([p.text for p in ocr_result.pages])

            # 2. Criteria Extraction
            criteria = await criteria_extraction_service.extract_criteria(db, document_id, full_text)

            # 3. Status Update
            if db_doc:
                db_doc.status = "processed"
                db.commit()

            # Log to Audit
            await audit_service.log_action(
                db=db,
                action="TENDER_RULES_EXTRACTED",
                user="PipelineEngine",
                document_id=document_id,
                changes={"criteria_count": len(criteria)}
            )

            logger.info(f"✅ Tender Rules extracted successfully for document: {document_id}")
            return criteria
        except Exception as e:
            logger.error(f"❌ Tender Pipeline failed: {str(e)}")
            if db_doc:
                db_doc.status = "failed"
                db.commit()
            await audit_service.log_action(
                db=db,
                action="TENDER_PIPELINE_FAILED",
                user="PipelineEngine",
                document_id=document_id,
                changes={"error": str(e)}
            )
            raise e

    async def run_bidder_pipeline(self, db: Session, document_id: str):
        """
        Orchestrates: OCR -> Bidder Entity Extraction -> Evaluation -> Explainability
        """
        logger.info(f"🚀 Starting Bidder Pipeline (Evidence & Matching) for: {document_id}")
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        try:
            # 1. OCR Layer
            ocr_result = await ocr_service.process_document(db, document_id)
            full_text = " ".join([p.text for p in ocr_result.pages])

            # 2. Bidder Entity Extraction (Evidence)
            evidence = await bidder_entity_service.extract_and_normalize(full_text, document_id)

            # 3. Evaluation Layer (Matches against parent tender rules)
            eval_result = await evaluation_engine_service.evaluate_bidder(db, document_id)

            # 4. Status Update
            if db_doc:
                db_doc.status = "processed"
                db.commit()

            # Log to Audit
            await audit_service.log_action(
                db=db,
                action="BIDDER_PIPELINE_COMPLETED",
                user="PipelineEngine",
                document_id=document_id,
                changes={"overall_score": eval_result.overall_score}
            )

            logger.info(f"✅ Bidder Evaluation completed successfully for document: {document_id}")
            return eval_result

        except Exception as e:
            logger.error(f"❌ Bidder Pipeline failed for document {document_id}: {str(e)}")
            if db_doc:
                db_doc.status = "failed"
                db.commit()
            await audit_service.log_action(
                db=db,
                action="BIDDER_PIPELINE_FAILED",
                user="PipelineEngine",
                document_id=document_id,
                changes={"error": str(e)}
            )
            raise e

tender_pipeline = TenderPipeline()
