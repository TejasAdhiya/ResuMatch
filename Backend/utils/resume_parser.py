import io
from docx import Document
import os
import re
import pdfplumber
import docx
from typing import Optional

def extract_resume_text(file_content: bytes, file_name: str) -> str:
    """Extract text from resume file (PDF or DOCX) with robust PDF extraction and OCR fallback."""
    try:
        if file_name.lower().endswith('.pdf'):
            import pdfplumber
            import pytesseract
            from pdf2image import convert_from_bytes
            text_pages = []
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                    if not page_text:
                        words = page.extract_words()
                        if words:
                            page_text = " ".join(word['text'] for word in words)
                    if not page_text:
                        # OCR fallback for this page
                        images = convert_from_bytes(file_content, first_page=i+1, last_page=i+1)
                        if images:
                            ocr_text = pytesseract.image_to_string(images[0])
                            if ocr_text.strip():
                                page_text = ocr_text
                    if page_text:
                        text_pages.append(page_text)
            text = "\n".join(text_pages)
        elif file_name.lower().endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_content))
            text = "\n".join(para.text for para in doc.paragraphs if para.text)
        else:
            raise ValueError("Unsupported file format")
        return text if text else ""
    except Exception as e:
        raise ValueError(f"Error extracting text: {str(e)}")

def extract_email_from_resume(text: str) -> Optional[str]:
    """Extract email address from resume text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None