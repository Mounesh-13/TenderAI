from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api.router import api_router
from app.database import engine, Base
from app.models import db_models
from app.config import settings
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI system for tender evaluation",
    version=settings.VERSION,
)

# Minimal Demo UI
static_content = """
<!DOCTYPE html>
<html>
<head>
    <title>TenderAI - Evaluation UI</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 30px auto; padding: 20px; background: #f8f9fa; color: #333; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1 { color: #0056b3; text-align: center; margin-bottom: 30px; }
        h2 { color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; margin-top: 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .btn { background: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; font-weight: 600; transition: 0.2s; width: 100%; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #6c757d; cursor: not-allowed; }
        input[type="file"] { margin: 15px 0; display: block; border: 1px solid #ddd; padding: 10px; width: 95%; border-radius: 4px; }
        #status-bar { padding: 15px; border-radius: 5px; font-weight: bold; margin-bottom: 20px; text-align: center; display: none; }
        .status-info { background: #d1ecf1; color: #0c5460; }
        .status-success { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .result-box { background: #f1f3f5; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; margin-top: 15px; border-left: 5px solid #007bff; }
        .loading { border: 3px solid #f3f3f3; border-top: 3px solid #007bff; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; margin-right: 10px; vertical-align: middle; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>TenderAI Evaluation Portal</h1>

    <div id="status-bar"></div>

    <div class="card" id="auth-box">
        <h2>1. Authentication</h2>
        <p>Initialize system access for the evaluation session.</p>
        <button class="btn" onclick="authenticate()">Auto-Login (Demo Admin)</button>
    </div>

    <div id="upload-grid" class="grid" style="display:none;">
        <div class="card">
            <h2>2. Tender Document</h2>
            <p>Upload the Master Tender PDF to extract rules.</p>
            <input type="file" id="tender-file" accept=".pdf">
            <button class="btn" id="tender-btn" onclick="processTender()">Process Tender</button>
        </div>
        <div class="card" id="bidder-box" style="opacity: 0.5; pointer-events: none;">
            <h2>3. Bidder Response</h2>
            <p>Upload Vendor response to match against rules.</p>
            <input type="file" id="bidder-file" accept=".pdf">
            <button class="btn" id="bidder-btn" onclick="processBidder()">Evaluate Bidder</button>
        </div>
    </div>

    <div class="card" id="result-box" style="display:none;">
        <h2>4. Evaluation Intelligence</h2>
        <div id="result-content" class="result-box"></div>
        <div style="margin-top:20px; display: flex; gap: 10px;">
            <button class="btn" onclick="window.open('/docs', '_blank')" style="background: #6c757d;">Open API Specs</button>
            <button class="btn" id="pdf-btn" onclick="downloadPdf()">Download PDF Report</button>
        </div>
    </div>

    <script>
        let token = "";
        let tenderId = "";
        let bidderId = "";

        function showStatus(msg, type) {
            const bar = document.getElementById('status-bar');
            bar.style.display = 'block';
            bar.className = 'status-' + type;
            bar.innerHTML = msg;
        }

        async function authenticate() {
            showStatus('<div class="loading"></div> Establishing secure connection...', 'info');
            try {
                await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: "demo@tender.ai", password: "password123", full_name: "Demo Admin", role: "admin"})
                });
                const resp = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'username=demo@tender.ai&password=password123'
                });
                const data = await resp.json();
                token = data.access_token;
                document.getElementById('auth-box').style.display = 'none';
                document.getElementById('upload-grid').style.display = 'grid';
                showStatus('Authentication successful. Ready for document ingestion.', 'success');
            } catch (e) {
                showStatus('Authentication failed: ' + e.message, 'error');
            }
        }

        async function processTender() {
            const file = document.getElementById('tender-file').files[0];
            if (!file) return alert("Select Tender PDF first");
            
            showStatus('<div class="loading"></div> Uploading Tender Document...', 'info');
            const formData = new FormData();
            formData.append('file', file);

            try {
                const up = await fetch('/api/v1/ingestion/upload?doc_type=tender', {
                    method: 'POST', headers: {'Authorization': 'Bearer ' + token}, body: formData
                });
                const data = await up.json();
                if (!data.metadata) throw new Error(data.detail || "Upload failed");
                tenderId = data.metadata.document_id;

                showStatus('<div class="loading"></div> AI Extracting Compliance Rules...', 'info');
                await fetch('/api/v1/pipelines/process/' + tenderId + '?run_sync=true', {
                    method: 'POST', headers: {'Authorization': 'Bearer ' + token}
                });

                showStatus('Tender processed. Rules extracted. Now upload bidder response.', 'success');
                document.getElementById('bidder-box').style.opacity = '1';
                document.getElementById('bidder-box').style.pointerEvents = 'all';
            } catch (e) {
                showStatus('Tender error: ' + e.message, 'error');
            }
        }

        async function processBidder() {
            const file = document.getElementById('bidder-file').files[0];
            if (!file) return alert("Select Bidder PDF first");
            
            showStatus('<div class="loading"></div> Analyzing Bidder Evidence...', 'info');
            const formData = new FormData();
            formData.append('file', file);

            try {
                const up = await fetch('/api/v1/ingestion/upload?doc_type=bidder&parent_tender_id=' + tenderId, {
                    method: 'POST', headers: {'Authorization': 'Bearer ' + token}, body: formData
                });
                const data = await up.json();
                if (!data.metadata) throw new Error(data.detail || "Upload failed");
                bidderId = data.metadata.document_id;

                showStatus('<div class="loading"></div> Running Compliance Engine...', 'info');
                await fetch('/api/v1/pipelines/process/' + bidderId + '?run_sync=true', {
                    method: 'POST', headers: {'Authorization': 'Bearer ' + token}
                });

                showStatus('Evaluation complete! Intelligence report generated.', 'success');
                showReport();
            } catch (e) {
                showStatus('Evaluation error: ' + e.message, 'error');
            }
        }

        async function showReport() {
            const resp = await fetch('/api/v1/reporting/report/' + bidderId, {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const report = await resp.json();
            const output = document.getElementById('result-content');
            
            let text = "AI VERDICT: " + (report.ai_evaluation.overall_score * 100).toFixed(1) + "% MATCH\\n\\n";
            text += "EVIDENCE CHAIN:\\n";
            report.evidence_chains.forEach(c => {
                text += " - " + c.summary + "\\n";
            });
            
            output.innerText = text;
            document.getElementById('result-box').style.display = 'block';
        }

        async function downloadPdf() {
            const btn = document.getElementById('pdf-btn');
            btn.disabled = true;
            try {
                const resp = await fetch('/api/v1/reporting/report/' + bidderId + '/pdf', {
                    headers: {'Authorization': 'Bearer ' + token}
                });
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `TenderAI_Report_${bidderId}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (e) {
                alert("PDF Download failed: " + e.message);
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return static_content

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
