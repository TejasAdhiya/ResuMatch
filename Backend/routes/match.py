from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from utils.matcher import calculate_match
from utils.resume_parser import extract_resume_text
from utils.resume_updater import update_resume_with_suggestions, cleanup_temp_file
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Enhanced endpoint to handle resume and job description analysis with comprehensive error handling.
    """
    try:
        logger.info("=== STARTING RESUME ANALYSIS ===")
        logger.info(f"File: {file.filename}")
        logger.info(f"Job description length: {len(job_description)}")
        
        # Validate inputs
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        if len(job_description.strip()) < 50:
            raise HTTPException(status_code=400, detail="Job description too short (minimum 50 characters required)")
        
        # Extract resume text
        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")
        
        resume_text = extract_resume_text(contents, file.filename)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from resume. Please ensure the file is readable and contains text content.")
        
        logger.info(f"Extracted resume text length: {len(resume_text)}")
        
        # Calculate match with enhanced error handling
        try:
            result = await calculate_match(resume_text, job_description)
        except ValueError as ve:
            logger.error(f"Validation error in matching: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as me:
            logger.error(f"Error in matching calculation: {me}")
            raise HTTPException(status_code=500, detail="Unable to process resume analysis. Please try again.")

        # Validate and enhance results
        result = validate_and_enhance_results(result)

        # Comprehensive debug output
        logger.info("\n=== FINAL BACKEND RESULTS ===")
        logger.info(f"Similarity Score: {result['similarity_score']}%")
        logger.info(f"Matched Keywords ({len(result['matched_keywords'])}): {result['matched_keywords'][:10]}")
        logger.info(f"Missing Keywords ({len(result['missing_keywords'])}): {result['missing_keywords'][:10]}")
        logger.info(f"Suggestions Length: {len(result['suggestion'])} characters")
        logger.info("Suggestions Preview:")
        logger.info(result['suggestion'][:300] + "..." if len(result['suggestion']) > 300 else result['suggestion'])
        logger.info("===============================\n")

        return {
            "similarity_score": result["similarity_score"],
            "matched_keywords": result["matched_keywords"],
            "missing_keywords": result["missing_keywords"],
            "suggestion": result["suggestion"]
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in processing: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during resume processing")

@router.post("/update-resume")
async def update_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Update the resume with AI suggestions and missing keywords.
    Only supports DOCX files.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail="Only DOCX files can be automatically updated. Please convert your resume to DOCX format."
            )

        # Read file contents
        contents = await file.read()
        
        # Extract text and calculate match
        resume_text = extract_resume_text(contents, file.filename)
        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume. Please ensure the file is readable."
            )

        # Get analysis results
        result = await calculate_match(resume_text, job_description)
        
        # Update the resume with suggestions
        updated_file_path = update_resume_with_suggestions(
            contents,
            result["missing_keywords"],
            result["suggestion"],
            job_description
        )

        # Schedule cleanup of the temporary file
        background_tasks.add_task(cleanup_temp_file, updated_file_path)

        # Return the updated file
        return FileResponse(
            updated_file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"Updated_{file.filename}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the resume. Please try again."
        )

def validate_and_enhance_results(result):
    """Validate and enhance the results before sending to frontend"""
    
    # Ensure similarity score is reasonable
    if not isinstance(result.get("similarity_score"), (int, float)) or result["similarity_score"] < 0:
        result["similarity_score"] = 50.0
    elif result["similarity_score"] > 100:
        result["similarity_score"] = 95.0
    
    # Ensure keywords are lists
    if not isinstance(result.get("matched_keywords"), list):
        result["matched_keywords"] = []
    if not isinstance(result.get("missing_keywords"), list):
        result["missing_keywords"] = []
    
    # Clean up keywords (remove empty strings, duplicates)
    result["matched_keywords"] = list(set([kw.strip() for kw in result["matched_keywords"] if kw.strip()]))[:15]
    result["missing_keywords"] = list(set([kw.strip() for kw in result["missing_keywords"] if kw.strip()]))[:10]
    
    # Ensure suggestions exist and are substantial
    if not result.get("suggestion") or len(result["suggestion"].strip()) < 200:
        logger.warning("Insufficient suggestions received")
        raise Exception("AI suggestions generation failed")
    
    return result