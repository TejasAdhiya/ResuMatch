from PyPDF2 import PdfReader
from docx import Document
import os
import io

def extract_text_from_pdf(contents: bytes):
    reader = PdfReader(io.BytesIO(contents))
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text

def extract_text_from_docx(contents: bytes):
    doc = Document(io.BytesIO(contents))
    return '\n'.join([para.text for para in doc.paragraphs])

def extract_resume_text(contents: bytes, filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(contents)
    elif ext == '.docx':
        return extract_text_from_docx(contents)
    else:
        raise ValueError("Unsupported file type")
