import re
from utils.file_handler import FileHandler

# List of Indian states for validation
INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry', 'Chandigarh',
    'Andaman and Nicobar Islands', 'Dadra and Nagar Haveli', 'Daman and Diu',
    'Lakshadweep'
]

def validate_input(file, state):
    """Validate file and state inputs"""
    
    # Validate file
    if not file:
        return "Resume file is required"
    
    file_handler = FileHandler()
    file_error = file_handler.validate_file(file)
    if file_error:
        return file_error
    
    # Validate state
    if not state:
        return "State selection is required"
    
    if state not in INDIAN_STATES:
        return f"Invalid state. Please select a valid Indian state"
    
    return None

def validate_email(email):
    """Validate email format"""
    if not email:
        return "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return "Invalid email format"
    
    return None

def validate_phone(phone):
    """Validate phone number format (Indian)"""
    if not phone:
        return None  # Phone is optional
    
    # Remove spaces and special characters
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Check for Indian phone number patterns
    patterns = [
        r'^\+91[6-9]\d{9}$',  # +91 followed by 10 digits starting with 6-9
        r'^[6-9]\d{9}$',      # 10 digits starting with 6-9
        r'^0[6-9]\d{9}$'      # 0 followed by 10 digits starting with 6-9
    ]
    
    if not any(re.match(pattern, clean_phone) for pattern in patterns):
        return "Invalid phone number format"
    
    return None

def sanitize_input(text):
    """Sanitize text input to prevent XSS and other attacks"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags and their content
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    return text.strip()

def validate_keywords(keywords):
    """Validate job keywords"""
    if not keywords:
        return "Job keywords are required"
    
    if len(keywords) < 2:
        return "At least 2 characters required for keywords"
    
    if len(keywords) > 100:
        return "Keywords too long (max 100 characters)"
    
    return None