from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure file upload
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Import and register blueprints
try:
    from routes.linkedin_jobs import linkedin_bp
    app.register_blueprint(linkedin_bp)
    logger.info("LinkedIn jobs blueprint registered successfully")
except ImportError as e:
    logger.error(f"Failed to import LinkedIn jobs blueprint: {e}")

# Keep your existing route for backwards compatibility
@app.route('/api/fetch-linkedin-jobs', methods=['POST'])
def fetch_linkedin_jobs_legacy():
    """Legacy endpoint - redirects to new blueprint"""
    try:
        from services.openai_service import OpenAIService
        from services.linkedin_scraper import LinkedInScraper
        from services.job_matcher import JobMatcher
        from utils.file_handler import FileHandler
        from utils.validators import validate_input
        
        # Initialize services
        openai_service = OpenAIService(os.getenv('OPENAI_API_KEY'))
        linkedin_scraper = LinkedInScraper()
        job_matcher = JobMatcher(openai_service)
        file_handler = FileHandler()
        
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['file']
        state = request.form.get('state')
        
        # Validate inputs
        validation_error = validate_input(file, state)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Step 1: Extract text from resume
        logger.info("Extracting text from resume...")
        resume_text = file_handler.extract_text(file)
        
        # Step 2: Analyze resume with OpenAI
        logger.info("Analyzing resume with AI...")
        resume_analysis = openai_service.analyze_resume(resume_text)
        
        # Step 3: Scrape LinkedIn jobs based on analysis and state
        logger.info(f"Scraping LinkedIn jobs for {state}...")
        raw_jobs = linkedin_scraper.search_jobs(
            keywords=resume_analysis['job_keywords'],
            location=state,
            limit=20  # Get more to filter down to best 5
        )
        
        # Step 4: Match and rank jobs using AI
        logger.info("Matching jobs with resume...")
        matched_jobs = job_matcher.rank_jobs(resume_text, raw_jobs, top_n=5)
        
        # Step 5: Format response
        response = {
            'success': True,
            'analysis': {
                'job_title': resume_analysis['predicted_job_title'],
                'skills': resume_analysis['key_skills'],
                'experience_level': resume_analysis['experience_level']
            },
            'jobs': matched_jobs,
            'total_found': len(raw_jobs),
            'state': state
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': 'An error occurred while processing your request',
            'details': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'ResuMatch backend is running',
        'version': '2.0'
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'ResuMatch API Server',
        'version': '2.0',
        'endpoints': {
            'health': '/api/health',
            'linkedin_jobs': '/api/fetch-linkedin-jobs',
            'linkedin_health': '/api/linkedin-jobs/health'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'HTTP method not allowed'}), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 10MB'}), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error occurred'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting ResuMatch server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)