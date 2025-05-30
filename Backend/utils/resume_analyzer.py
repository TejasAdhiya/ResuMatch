import openai
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv
import PyPDF2
import io
import traceback
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes

load_dotenv()

class ResumeAnalyzer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        """Extract text from PDF file bytes using pdfplumber, with OCR fallback for image-based pages."""
        try:
            text_pages = []
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                    if not page_text:
                        words = page.extract_words()
                        if words:
                            page_text = " ".join(word['text'] for word in words)
                    if not page_text:
                        # OCR fallback for this page
                        images = convert_from_bytes(pdf_file, first_page=i+1, last_page=i+1)
                        if images:
                            ocr_text = pytesseract.image_to_string(images[0])
                            if ocr_text.strip():
                                page_text = ocr_text
                    if page_text:
                        text_pages.append(page_text)
            text = "\n".join(text_pages)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF (with OCR): {str(e)}")
            traceback.print_exc()
            return ""

    def extract_email(self, text: str) -> str:
        """Extract email from resume text using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the email address from the following resume text. Return only the email address, nothing else."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error extracting email: {str(e)}")
            traceback.print_exc()
            return ""

    def extract_name(self, text: str) -> str:
        """Extract name from resume text using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the full name from the following resume text. Return only the name, nothing else."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error extracting name: {str(e)}")
            traceback.print_exc()
            return ""

    async def analyze_resume(self, resume_text: str, job_description: str) -> Tuple[float, str]:
        """Analyze resume against job description and return match score and analysis."""
        try:
            prompt = f"""
            You are a strict and objective resume evaluator. Analyze the following resume against the job description and provide:
            1. A match score from 0 to 100 (be strict: only give a score above 70 if the resume is an excellent, near-perfect fit; most resumes should score below 50 unless they are a strong match)
            2. A brief, professional analysis of why the score was given
            3. Key strengths and weaknesses in relation to the job requirements

            Resume:
            {resume_text}

            Job Description:
            {job_description}

            Format your response as:
            Score: [number]
            Analysis: [your analysis]
            Key strengths: [bulleted or short list]
            Key weaknesses: [bulleted or short list]
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume analyzer."},
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content.strip()
            
            # Extract score from the response
            score_line = analysis.split('\n')[0]
            score = float(score_line.split(':')[1].strip())

            return score, analysis
        except Exception as e:
            print(f"Error analyzing resume: {str(e)}")
            traceback.print_exc()
            return 0.0, "Error analyzing resume"

    async def analyze_bulk_resumes(self, resumes: List[bytes], job_description: str) -> List[Dict]:
        """Analyze multiple resumes and return results."""
        results = []
        
        for resume_bytes in resumes:
            resume_text = self.extract_text_from_pdf(resume_bytes)
            email = self.extract_email(resume_text)
            name = self.extract_name(resume_text)
            score, analysis = await self.analyze_resume(resume_text, job_description)
            
            results.append({
                "name": name,
                "email": email,
                "score": score,
                "analysis": analysis
            })
        
        return results 