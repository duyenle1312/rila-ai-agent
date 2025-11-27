from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
import mammoth
import re
from io import BytesIO
import uvicorn

# modules
from app.services.llm import summarize_text
from app.services.notifier import send_email_notification
from app.services.notion import create_notion_page

app = FastAPI()


# Allow your React dev server (localhost:5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
#  WebSocket connection manager
# --------------------------------------------------------
class JobConnectionManager:
    def __init__(self):
        # job_id => WebSocket
        self.active_jobs: dict[str, WebSocket] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_jobs[job_id] = websocket

    def disconnect(self, job_id: str):
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]

    async def send_step(self, job_id: str, step: str, detail: str = ""):
        """
        Send JSON timeline event to client.
        React expects: { step, detail, timestamp }
        """
        if job_id not in self.active_jobs:
            return

        ws = self.active_jobs[job_id]

        await ws.send_json({
            "step": step,
            "detail": detail,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"
        })

manager = JobConnectionManager()

# --------------------------------------------------------
# Helper: DOCX → HTML
# --------------------------------------------------------
def convert_docx_to_html(file_bytes: bytes) -> str:
    docx_file = BytesIO(file_bytes)
    result = mammoth.convert_to_html(docx_file)
    return result.value

pending_jobs = {}
# --------------------------------------------------------
# Upload endpoint expected by React frontend
# --------------------------------------------------------
@app.post("/upload")
async def upload_docx(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.endswith(".docx"):
        return {"error": "Only .docx files supported."}

    # Create job_id for WebSocket
    job_id = str(uuid.uuid4())

    filename = file.filename.replace(".docx", "")
    filename = re.sub(r"[^A-Za-z0-9 ]+", "", filename)

    file_bytes = await file.read()
    html_content = convert_docx_to_html(file_bytes)

    # store job in memory; wait for websocket "start" msg
    pending_jobs[job_id] = {
        "title": filename,
        "html": html_content
    }

    # Background processing
    # background_tasks.add_task(run_processing_pipeline, job_id, filename, html_content)

    # This URL will be opened by the React WebSocket client
    return {
        "job_id": job_id,
        "ws_path": f"/ws/process/{job_id}",
        "filename": file.filename,
        "status": "processing"
    }


# --------------------------------------------------------
# 🔥 Background Pipeline (Sends events to WebSocket)
# --------------------------------------------------------
async def run_processing_pipeline(job_id: str, title: str, html_content: str):
    # Notify step 1
    await manager.send_step(job_id, "Step 1: Created HTML", f"Extracted HTML from DOCX")

    # Step 2 — LLM Summary
    await manager.send_step(job_id, "Step 2: Summarizing", "Calling Gemini...")

    llm_response = await summarize_text(
        title=title,
        html_content=html_content
    )

    await manager.send_step(job_id, "Step 2: Summary created", "Gemini summary completed")

    # Step 3 — Notion Page
    await manager.send_step(job_id, "Step 3: Creating Notion page", "Sending data to Notion API")

    notion_response = await create_notion_page(
        title=title,
        slug=llm_response["slug"],
        ai_summary=llm_response["ai_summary"],
        seo_keywords=llm_response["seo_keywords"],
        coverImg=llm_response["cover_imgUrl"],
        html_content=llm_response["html_content"]
    )

    if notion_response["status"] == "success":
        await manager.send_step(job_id, "Step 3: Notion page created", notion_response["url"])
    else:
        await manager.send_step(job_id, "Error", "Failed to create Notion page")

    # Step 4 — Email Notification
    await manager.send_step(job_id, "Step 4: Sending email", "Sending email confirmation...")
    send_email_notification(title, notion_response.get("url", ""))

    await manager.send_step(job_id, "Step 5: Email sent to duyen@rilaglobal.com", "Upload blog successfully!")

    # Properly close WS
    ws = manager.active_jobs.get(job_id)
    if ws:
        await ws.close()
    manager.disconnect(job_id)




# --------------------------------------------------------
# WebSocket endpoint
# --------------------------------------------------------
@app.websocket("/ws/process/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    # Register WS
    manager.active_jobs[job_id] = websocket

    # initial message
    await manager.send_step(job_id, "WebSocket connected", f"Job {job_id}")

    try:
        while True:
            try:
                msg = await websocket.receive_text()

                if msg == "start":
                    # Start pipeline ONLY NOW
                    data = pending_jobs.pop(job_id, None)
                    if data:
                        title = data["title"]
                        html_content = data["html"]
                        await run_processing_pipeline(job_id, title, html_content)
                    else:
                        await manager.send_step(job_id, "Error", "Job not found")
            except RuntimeError:
                # WebSocket was closed
                break

    except WebSocketDisconnect:
        manager.disconnect(job_id)


# --------------------------------------------------------
# Root
# --------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to RILA's Notion Blog Agent API!"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
