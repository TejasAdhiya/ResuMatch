from flask import Blueprint, request, jsonify
import os
import logging
from services.openai_service import OpenAIService
from services.linkedin_scraper import LinkedInScraper
from services.job_matcher import JobMatcher
from utils.file_handler import FileHandler
from utils.validators import validate_input

# Create blueprint
linkedin_bp = Blueprint('linkedin', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
openai_service = OpenAIService(os.getenv('OPENAI_API_KEY'))
linkedin_scraper = LinkedInScraper()
job_matcher = JobMatcher(openai_service)
file_handler = FileHandler()

@linkedin_bp.route('/api/fetch-linkedin-jobs', methods=['POST'])
def fetch_linkedin_jobs():
    """
    Main endpoint to fetch LinkedIn jobs based on resume analysis
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['file']
        state = request.form.get('state')
        
        logger.info(f"Processing request for state: {state}")
        
        # Validate inputs
        validation_error = validate_input(file, state)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Step 1: Extract text from resume
        logger.info("Extracting text from resume...")
        resume_text = file_handler.extract_text(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({'error': 'Resume appears to be empty or too short. Please upload a detailed resume.'}), 400
        
        # Step 2: Analyze resume with OpenAI
        logger.info("Analyzing resume with AI...")
        resume_analysis = openai_service.analyze_resume(resume_text)
        
        if not resume_analysis:
            return jsonify({'error': 'Failed to analyze resume. Please try again.'}), 500
        
        # Step 3: Generate search keywords from analysis
        job_keywords = resume_analysis.get('job_keywords', [])
        predicted_job_title = resume_analysis.get('predicted_job_title', '')
        
        if not job_keywords and predicted_job_title:
            job_keywords = [predicted_job_title]
        
        if not job_keywords:
            job_keywords = ['software developer', 'analyst']  # fallback
        
        logger.info(f"Generated keywords: {job_keywords}")
        
        # Step 4: Scrape LinkedIn jobs based on analysis and state
        logger.info(f"Scraping LinkedIn jobs for {state}...")
        raw_jobs = linkedin_scraper.search_jobs(
            keywords=job_keywords,
            location=state,
            limit=20  # Get more to filter down to best 5
        )
        
        if not raw_jobs:
            return jsonify({
                'error': f'No jobs found for your profile in {state}. Try selecting a different state or update your resume with more relevant skills.',
                'analysis': {
                    'job_title': resume_analysis.get('predicted_job_title', ''),
                    'skills': resume_analysis.get('key_skills', []),
                    'experience_level': resume_analysis.get('experience_level', '')
                }
            }), 404
        
        logger.info(f"Found {len(raw_jobs)} raw jobs")
        
        # Step 5: Match and rank jobs using AI
        logger.info("Matching jobs with resume...")
        matched_jobs = job_matcher.rank_jobs(resume_text, raw_jobs, top_n=5)
        
        if not matched_jobs:
            return jsonify({
                'error': 'No suitable job matches found. Please try updating your resume or selecting a different state.',
                'analysis': {
                    'job_title': resume_analysis.get('predicted_job_title', ''),
                    'skills': resume_analysis.get('key_skills', []),
                    'experience_level': resume_analysis.get('experience_level', '')
                }
            }), 404
        
        # Step 6: Format response
        response = {
            'success': True,
            'message': f'Found {len(matched_jobs)} highly relevant job opportunities for you!',
            'analysis': {
                'job_title': resume_analysis.get('predicted_job_title', 'Professional'),
                'skills': resume_analysis.get('key_skills', []),
                'experience_level': resume_analysis.get('experience_level', 'Mid-level'),
                'job_keywords': job_keywords
            },
            'jobs': matched_jobs,
            'total_found': len(raw_jobs),
            'state': state,
            'filtered_count': len(matched_jobs)
        }
        
        logger.info(f"Successfully processed request. Returning {len(matched_jobs)} jobs")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing LinkedIn jobs request: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request. Please try again.',
            'details': str(e) if os.getenv('FLASK_DEBUG') else None
        }), 500

@linkedin_bp.route('/api/linkedin-jobs/health', methods=['GET'])
def linkedin_health_check():
    """Health check endpoint for LinkedIn jobs service"""
    try:
        # Test OpenAI connection
        if not os.getenv('OPENAI_API_KEY'):
            raise Exception("OpenAI API key not configured")
        
        return jsonify({
            'status': 'healthy',
            'message': 'LinkedIn jobs service is running',
            'services': {
                'openai': 'connected',
                'scraper': 'ready',
                'matcher': 'ready'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@linkedin_bp.route('/api/linkedin-jobs/test-analysis', methods=['POST'])
def test_resume_analysis():
    """Test endpoint for resume analysis only"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['file']
        
        # Extract text
        resume_text = file_handler.extract_text(file)
        
        # Analyze with OpenAI
        analysis = openai_service.analyze_resume(resume_text)
        
        return jsonify({
            'success': True,
            'resume_length': len(resume_text),
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers for the blueprint
@linkedin_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@linkedin_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@linkedin_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Please upload files smaller than 10MB'}), 413