import tempfile
from docx import Document
import pdfplumber

def extract_text_from_pdf(content: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        with pdfplumber.open(tmp.name) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text

def extract_text_from_docx(content: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        doc = Document(tmp.name)
        return "\n".join(p.text for p in doc.paragraphs)