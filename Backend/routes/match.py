from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.matcher import calculate_match
from utils.resume_parser import extract_resume_text

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Endpoint to handle resume and job description, and calculate match results.
    """
    try:
        contents = await file.read()
        resume_text = extract_resume_text(contents, file.filename)
        result = calculate_match(resume_text, job_description)

        # Ensure result contains all required fields
        response = {
            "similarity_score": result.get("similarity_score", 0.0),
            "matched_keywords": result.get("matched_keywords", []),
            "missing_keywords": result.get("missing_keywords", []),
            "suggestion": result.get("suggestion", ""),
        }

        return response

    except Exception as e:
        print(f"Error in processing: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
