from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re

# Initialize the transformer model for semantic similarity
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

# Predefined set of industry-level keywords
INDUSTRY_KEYWORDS = {
    "team", "development", "design", "management", "leadership", "testing",
    "research", "analysis", "strategy", "marketing", "data", "operations",
    "programming", "frontend", "backend", "AI", "machine learning",
    "project management", "cloud", "security", "optimization", "UI", "UX",
    "testing", "devops", "business", "sales", "communication", "customer"
}

# Stopwords and punctuation
STOPWORDS = set(stopwords.words('english'))
PUNCTUATION = set(string.punctuation)

def preprocess_text(text):
    """
    Preprocess text by removing stopwords, punctuation, and lemmatizing words.
    """
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = word_tokenize(text)
    filtered_words = [word for word in words if word not in STOPWORDS and word not in PUNCTUATION]
    return " ".join(filtered_words)

async def calculate_match(resume_text, job_description):
    """
    Calculate similarity score, extract keywords, and provide suggestions for improvement.
    """
    # Preprocess texts
    resume_cleaned = preprocess_text(resume_text)
    job_cleaned = preprocess_text(job_description)

    # Calculate semantic similarity
    resume_embedding = semantic_model.encode(resume_text)
    job_embedding = semantic_model.encode(job_description)
    semantic_similarity_score = cosine_similarity([resume_embedding], [job_embedding])[0][0] * 100

    # Calculate keyword-based match score
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_cleaned, job_cleaned])
    keyword_similarity_score = cosine_similarity(vectors[0], vectors[1])[0][0] * 100

    # Combine the scores
    final_score = (0.8 * semantic_similarity_score) + (0.2 * keyword_similarity_score)

    # Extract keywords
    job_keywords = set(job_cleaned.split()) & INDUSTRY_KEYWORDS
    resume_keywords = set(resume_cleaned.split()) & INDUSTRY_KEYWORDS
    matched_keywords = list(job_keywords.intersection(resume_keywords))
    missing_keywords = list(job_keywords - resume_keywords)

    # Predefined suggestions
    suggestions = []
    if not re.search(r"project|projects|portfolio", resume_cleaned):
        suggestions.append("✨ Consider adding projects to showcase your hands-on experience.")
    if not re.search(r"certification|certifications|credential|credentials", resume_cleaned):
        suggestions.append("💡 Adding relevant certifications can boost your resume's credibility.")
    if not re.search(r"(\d+%|\$\d+|increased|reduced|achieved|grew|saved)", resume_cleaned):
        suggestions.append("🔍 Include quantifiable achievements to make your resume more impactful.")

    return {
        "similarity_score": round(final_score, 2),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestion": "\n".join(suggestions) if suggestions else "No suggestions available"
    }
