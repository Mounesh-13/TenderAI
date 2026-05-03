# TenderAI

Production-grade AI system for tender evaluation.

## Architecture
- Ingestion
- OCR
- NLP
- Evaluation
- Human-in-loop
- Audit

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `uvicorn app.main:app --reload`

## Docker Setup
1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
2. The API will be available at `http://localhost:8000`.
3. Swagger UI: `http://localhost:8000/docs`
