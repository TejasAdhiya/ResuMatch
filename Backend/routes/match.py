from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_route():
    return {"message": "Match route working"}

from fastapi import File, UploadFile
from utils.resume_parser import extract_resume_text
import os

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    file_location = f"temp_uploads/{file.filename}"
    os.makedirs("temp_uploads", exist_ok=True)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    extracted_text = extract_resume_text(file_location)
    return {"text": extracted_text[:1000]}  # Return only first 1000 chars for testing
