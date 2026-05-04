# 🚀 TenderAI: Production-Grade Automated Tender Evaluation

TenderAI is a sophisticated AI-driven system designed to automate the end-to-end evaluation of complex procurement documents. By leveraging Large Language Models (LLM), advanced OCR, and a rule-based evaluation engine, TenderAI transforms weeks of manual auditing into minutes of automated, audit-ready intelligence.

---

## 🌟 Key Features

- **6-Layer Production Architecture**: Modular design covering Ingestion, OCR, NLP, Evaluation, HITL, and Audit.
- **AI-Powered Criteria Extraction**: 3-pass pipeline using Google Gemini to extract complex requirements from tender PDFs.
- **Evidence-Chain Explainability**: Every AI score is linked to a specific text snippet and page number for 100% transparency.
- **Professional Evaluation Portal**: A modern web interface for document management and real-time evaluation tracking.
- **Human-in-the-Loop (HITL)**: Automated flagging of low-confidence AI decisions for human expert review.
- **Immutable Audit Trail**: Append-only JSON logging for regulatory compliance and procurement transparency.
- **Professional PDF Reporting**: Instant generation of evaluation summaries via a crash-proof binary streaming engine.

---

## 🏗️ Architecture Summary

1.  **Ingestion Layer**: Multi-format support (PDF, DOCX, Images) with automatic heuristic classification.
2.  **OCR Layer**: High-fidelity text extraction using `pdfplumber` and `pytesseract`.
3.  **NLP Layer**: Named Entity Recognition (NER) and requirement structured extraction.
4.  **Evaluation Layer**: Rule-based matching engine supporting complex mathematical comparators.
5.  **HITL Layer**: Workflow management for expert validation of AI verdicts.
6.  **Audit Layer**: Immuntable record-keeping of every system and user action.

---

## 🚀 Getting Started

### 📋 Prerequisites
- Python 3.10+
- Tesseract OCR (installed on your system)

### 🛠️ Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/TenderAI.git
    cd TenderAI
    ```

2.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```ini
    PROJECT_NAME=TenderAI
    DATABASE_URL=sqlite:///./tender_ai.db
    OCR_ENGINE=tesseract
    LLM_PROVIDER=gemini
    GEMINI_API_KEY=your_api_key_here
    SECRET_KEY=your_secret_key_for_jwt
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install email-validator bcrypt==4.0.1
    python -m spacy download en_core_web_sm
    ```

4.  **Run the Application**:
    ```bash
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    ```

---

## 🎥 Demo Instructions

1.  **Open the Portal**: Navigate to `http://localhost:8000/` in your browser.
2.  **Authenticate**: Click **"Auto-Login"** to initialize an admin session.
3.  **Process Tender**: Upload your `tender_doc.pdf`. The AI will extract evaluation rules (e.g., "Experience > 5 years").
4.  **Evaluate Bidders**: Upload vendor PDFs (e.g., `bidder_pass.pdf`). The system will match evidence against the rules.
5.  **View Intelligence**: Instantly see the **Evidence Chains** and **Overall Score**.
6.  **Export**: Download the **Audit-Ready PDF Report** for your records.

---

## 🛠️ Technical Fixes (Stability Phase)
- **Definitive PDF Stability**: Implemented a failsafe stream-rendering system to prevent PDF corruption.
- **Robust Character Encoding**: Standardized Latin-1 sanitization for universal document compatibility.
- **Backend Hardening**: Fixed critical NameErrors and Regex logic issues in the core pipeline.

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
