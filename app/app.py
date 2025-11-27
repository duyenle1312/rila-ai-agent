from fastapi import FastAPI, File, UploadFile, BackgroundTasks
import mammoth
import re
from docx import Document
from io import BytesIO
from app.services.llm import summarize_text
from app.services.notifier import send_email_notification
from app.services.notion import create_notion_page

app = FastAPI()


def convert_docx_to_html(file_bytes: bytes) -> str:
    docx_file = BytesIO(file_bytes)
    result = mammoth.convert_to_html(docx_file)
    return result.value


@app.post("/read-docx/")
async def read_docx(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):

    # Step 1 — Extract text from DOCX
    if not file.filename.endswith(".docx"):
        return {"error": "Unsupported file type. Only .docx files are supported."}

    filename = file.filename.replace(".docx", "")
    filename = re.sub(r'[^A-Za-z0-9 ]+', '', filename) # rm special chars

    file_bytes = await file.read()

    html_content = convert_docx_to_html(file_bytes)

    # Background task for sending to Notion + email
    background_tasks.add_task(create_notion_and_notify, filename, html_content)

    return {
        "title": filename,
        "status": "processing",
        "filename": file.filename
    }


async def create_notion_and_notify(title, html_content):
    # Step 2 — Summarize with Gemini
    llm_response = await summarize_text(title=title, html_content=html_content)

    # Step 3 — Send to Notion
    notion_response = await create_notion_page(title=title, slug=llm_response["slug"], ai_summary=llm_response["ai_summary"], seo_keywords=llm_response["seo_keywords"], coverImg=llm_response["cover_imgUrl"], html_content=llm_response["html_content"])

    # Step 4 - Send notification (WhatsApp / Email)
    if notion_response["status"] == "success":
        send_email_notification(title, notion_response["url"])
    else:
        print("Failed to create Notion page.")


@app.get("/")
def read_root():
    return {"message": "Welcome to RILA's Notion Blog Agent API!"}