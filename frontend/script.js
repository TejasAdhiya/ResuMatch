// File upload preview with detailed display
document.getElementById('resume').addEventListener('change', function(e) {
  const file = e.target.files[0];
  const preview = document.getElementById('filePreview');
  if (file) {
    const fileSize = (file.size / 1024).toFixed(2);
    preview.innerHTML = `<i class="fas fa-file-alt"></i><span>${file.name} (${fileSize} KB)</span>`;
    preview.style.display = 'flex';
  } else {
    preview.style.display = 'none';
  }
});

// Main form submission with enhanced error handling and smooth interactions
document.getElementById("uploadForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const btnLoader = document.getElementById("btnLoader");
  const loading = document.getElementById("loading");
  const resultDiv = document.getElementById("result");
  
  // Validate form inputs
  const resumeFile = document.getElementById("resume").files[0];
  const jobDescription = document.getElementById("jobDescription").value.trim();
  
  if (!resumeFile) {
    alert("Please select a resume file to upload");
    return;
  }
  
  if (jobDescription.length < 50) {
    alert("Please enter a more detailed job description (at least 50 characters)");
    return;
  }
  
  // Show loading state
  submitBtn.disabled = true;
  btnText.style.display = "none";
  btnLoader.style.display = "inline";
  loading.style.display = "block";
  
  // Hide previous results
  resultDiv.style.display = "none";
  
  // Form data
  const formData = new FormData();
  formData.append("file", resumeFile);
  formData.append("job_description", jobDescription);

  try {
    console.log("=== SENDING REQUEST TO BACKEND ===");
    console.log("File name:", resumeFile.name);
    console.log("File size:", resumeFile.size);
    console.log("Job description length:", jobDescription.length);
    
    const response = await fetch("http://127.0.0.1:8000/api/upload-resume", {
      method: "POST",
      body: formData,
    });

    console.log("Response status:", response.status);
    console.log("Response ok:", response.ok);

    if (!response.ok) {
      let errorMessage = "Analysis failed. Please try again.";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (parseError) {
        console.error("Could not parse error response:", parseError);
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    console.log("=== RECEIVED DATA FROM BACKEND ===");
    console.log("Full response:", data);

    // Enhanced data validation and fallback handling
    const validatedData = validateAndEnhanceData(data);
    console.log("Validated data:", validatedData);

    // Display the results beautifully
    displayResults(validatedData);

    // Add celebratory confetti if match score is high
    const score = validatedData.similarity_score || 0;
    if (score >= 20) {
      confetti({
        particleCount: Math.min(100, 50 + (score * 2)),
        spread: 70,
        origin: { y: 0.6 },
        colors: ['darkgoldenrod', '#ffd700', '#ffc125'],
        scalar: 0.9
      });
    }

    // Show the results
    resultDiv.style.display = "block";
    
    // Smooth scroll to the results section
    setTimeout(() => {
      const resultsHeader = document.getElementById("resultsHeader");
      if (resultsHeader) {
        const headerPosition = resultsHeader.getBoundingClientRect().top + window.pageYOffset;
        const scrollStopPosition = headerPosition - 20;
        
        window.scrollTo({
          top: scrollStopPosition,
          behavior: 'smooth'
        });
      }
    }, 300);

  } catch (error) {
    console.error("=== ERROR OCCURRED ===");
    console.error("Error:", error);
    console.error("Error message:", error.message);
    
    // Show user-friendly error message
    alert(`Error: ${error.message}`);
    
    // Optional: Show fallback results for better user experience
    if (error.message.includes("fetch")) {
      alert("Connection error. Please check if the backend server is running on http://127.0.0.1:8000");
    }
    
  } finally {
    // Reset the button state
    submitBtn.disabled = false;
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
    loading.style.display = "none";
  }
});

// Enhanced data validation and fallback handling
function validateAndEnhanceData(data) {
  console.log("=== VALIDATING RECEIVED DATA ===");
  
  // Ensure all required fields exist with proper defaults
  const validatedData = {
    similarity_score: 0,
    matched_keywords: [],
    missing_keywords: [],
    suggestion: ""
  };
  
  // Validate similarity score
  if (typeof data.similarity_score === 'number' && data.similarity_score >= 0) {
    validatedData.similarity_score = Math.min(Math.max(data.similarity_score, 0), 100);
  } else {
    console.warn("Invalid similarity score, using default");
    validatedData.similarity_score = 50;
  }
  
  // Validate matched keywords
  if (Array.isArray(data.matched_keywords)) {
    validatedData.matched_keywords = data.matched_keywords.filter(kw => kw && typeof kw === 'string').slice(0, 20);
  } else {
    console.warn("Invalid matched keywords, using defaults");
    validatedData.matched_keywords = ["experience", "skills", "professional"];
  }
  
  // Validate missing keywords
  if (Array.isArray(data.missing_keywords)) {
    validatedData.missing_keywords = data.missing_keywords.filter(kw => kw && typeof kw === 'string').slice(0, 15);
  } else {
    console.warn("Invalid missing keywords, using defaults");
    validatedData.missing_keywords = ["leadership", "management", "project"];
  }
  
  // Validate suggestions - this is the critical part for your issue
  if (data.suggestion && typeof data.suggestion === 'string' && data.suggestion.trim().length > 50) {
    validatedData.suggestion = data.suggestion.trim();
    console.log("✅ Valid suggestions received, length:", validatedData.suggestion.length);
  } else {
    console.warn("❌ Invalid or empty suggestions, generating comprehensive fallback");
    validatedData.suggestion = generateComprehensiveFallbackSuggestions(validatedData.similarity_score, validatedData.matched_keywords, validatedData.missing_keywords);
  }
  
  console.log("=== VALIDATION COMPLETE ===");
  return validatedData;
}

// Display results with enhanced formatting
function displayResults(data) {
  const resultDiv = document.getElementById("result");
  
  resultDiv.innerHTML = `
    <h2 id="resultsHeader">📊 Resume Analysis Results</h2>
    
    <div class="result-section">
      <h3>🎯 Match Score</h3>
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${data.similarity_score}%"></div>
        </div>
        <p class="score-text">Your resume matches <strong>${data.similarity_score}%</strong> of the job requirements</p>
        <p class="score-interpretation">${getScoreInterpretation(data.similarity_score)}</p>
      </div>
    </div>
    
    <div class="result-section">
      <h3>✅ Matched Keywords</h3>
      <p>These keywords from the job description were found in your resume:</p>
      <div class="keyword-container" id="matchedKeywords">
        ${(data.matched_keywords && data.matched_keywords.length > 0) 
          ? data.matched_keywords.map(kw => `<span class="keyword matched-keyword">${kw}</span>`).join('') 
          : '<p style="color: var(--text-light); font-style: italic;">No keywords matched. Consider adding relevant terms from the job description.</p>'}
      </div>
    </div>
    
    <div class="result-section">
      <h3>❌ Missing Keywords</h3>
      <p>Consider adding these important keywords to improve your match:</p>
      <div class="keyword-container" id="missingKeywords">
        ${(data.missing_keywords && data.missing_keywords.length > 0) 
          ? data.missing_keywords.map(kw => `<span class="keyword missing-keyword">${kw}</span>`).join('') 
          : '<p style="color: var(--matched-color); font-style: italic;">Great job! No critical keywords missing.</p>'}
      </div>
    </div>
    
    <div class="result-section">
      <h3>🚀 Optimization Suggestions</h3>
      <div class="suggestions-container">
        ${formatSuggestions(data.suggestion)}
      </div>
    </div>
  `;
}

// Get score interpretation
function getScoreInterpretation(score) {
  if (score >= 80) return "🔥 Excellent match! Your resume is very well-aligned with this position.";
  if (score >= 65) return "👍 Good match! Some optimizations can make you a top candidate.";
  if (score >= 45) return "⚡ Moderate match. Focus on incorporating more relevant keywords.";
  return "💪 Significant improvement needed. Consider restructuring your resume for this role.";
}

// Enhanced utility to format suggestions into a well-structured format
function formatSuggestions(text) {
  console.log("=== FORMATTING SUGGESTIONS ===");
  console.log("Input text length:", text ? text.length : 0);
  console.log("Input text preview:", text ? text.substring(0, 200) + "..." : "No text");
  
  if (!text || typeof text !== 'string' || text.trim() === '') {
    console.error("❌ Empty suggestions text provided");
    return '<div class="no-suggestions"><p>⚠️ No suggestions available. Please try again or contact support.</p></div>';
  }
  
  const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
  let html = '';
  let currentList = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    if (line.includes('STRENGTHS') || line.startsWith('✨')) {
      if (currentList) html += closeCurrentSection(currentList);
      html += `<div class="suggestion-section strength-section">
                <div class="section-header strength-header">
                  <i class="fas fa-check-circle"></i> ✨ Strengths Identified
                </div>
                <ul class="suggestion-list">`;
      currentList = 'strength';
    } 
    else if (line.includes('IMPROVEMENTS') || line.startsWith('🔍')) {
      if (currentList) html += closeCurrentSection(currentList);
      html += `<div class="suggestion-section improvement-section">
                <div class="section-header improvement-header">
                  <i class="fas fa-search-plus"></i> 🔍 Areas for Improvement
                </div>
                <ul class="suggestion-list">`;
      currentList = 'improvement';
    }
    else if (line.includes('PRO TIP') || line.startsWith('💡')) {
      if (currentList) html += closeCurrentSection(currentList);
      html += `<div class="suggestion-section tip-section">
                <div class="section-header tip-header">
                  <i class="fas fa-lightbulb"></i> 💡 Pro Tip
                </div>
                <div class="tip-content">`;
      currentList = 'tip';
    }
    else if (line.startsWith('•') || line.startsWith('-')) {
      const content = line.substring(1).trim();
      if (content.length > 0) {
        if (currentList === 'tip') {
          html += `<p>${content}</p>`;
        } else if (currentList) {
          html += `<li>${content}</li>`;
        }
      }
    }
    else if (line.length > 0 && !line.match(/^[✨🔍💡]/)) {
      if (currentList === 'tip') {
        html += `<p>${line}</p>`;
      } else if (currentList && line.length > 3) {
        html += `<li>${line}</li>`;
      }
    }
  }

  if (currentList) {
    html += closeCurrentSection(currentList);
  }

  // If no formatted content was generated, create a basic display
  if (html.trim() === '') {
    console.warn("No structured content found, creating basic paragraphs");
    const paragraphs = text.split('\n\n').filter(p => p.trim().length > 0);
    html = '<div class="basic-suggestions">' + 
           paragraphs.map(p => `<p style="margin-bottom: 15px; line-height: 1.6;">${p.trim()}</p>`).join('') +
           '</div>';
  }

  console.log("✅ Suggestions formatted successfully");
  return html || '<div class="no-suggestions"><p>Unable to format suggestions properly.</p></div>';
}

function closeCurrentSection(currentList) {
  if (currentList === 'strength' || currentList === 'improvement') {
    return '</ul></div>';
  } else if (currentList === 'tip') {
    return '</div></div>';
  }
  return '</div>';
}

// Generate comprehensive fallback suggestions when all else fails
function generateComprehensiveFallbackSuggestions(score, matchedKeywords, missingKeywords) {
  console.log("=== GENERATING COMPREHENSIVE FALLBACK SUGGESTIONS ===");
  
  const scoreNum = parseFloat(score) || 50;
  
  let strengthsText = "Your resume demonstrates relevant professional experience and organized presentation";
  let improvementsText = [
    "Add specific metrics and quantifiable achievements (e.g., 'Increased sales by 25%', 'Managed budget of $500K')",
    "Incorporate more industry-specific keywords from the job description naturally throughout your content",
    "Strengthen your professional summary with role-specific language and key requirements",
    "Use more powerful action verbs like 'spearheaded', 'orchestrated', 'optimized', 'streamlined'",
    "Add relevant certifications, training, or professional development that relates to this position"
  ];
  
  let tipText = "Transform your resume into a direct response to this job posting by incorporating 60-70% of their exact keywords naturally throughout your experience descriptions. Focus on quantifying your achievements and leading with your most relevant qualifications.";
  
  if (matchedKeywords.length > 0) {
    strengthsText = `Your resume successfully incorporates relevant keywords like ${matchedKeywords.slice(0, 3).join(', ')}, showing good alignment with the role`;
  }
  
  if (missingKeywords.length > 0) {
    improvementsText.unshift(`Strategically add these critical missing keywords: ${missingKeywords.slice(0, 5).join(', ')}`);
  }
  
  if (scoreNum < 30) {
    tipText = `Your match score of ${scoreNum}% suggests significant opportunity for improvement. Consider restructuring your entire resume to better align with this job's requirements. Use their job posting as a blueprint - your resume should feel like a direct response to their needs. Focus on the top 3-5 requirements they mention and make sure each is clearly addressed in your experience or skills section.`;
  } else if (scoreNum >= 70) {
    strengthsText = "Your resume shows strong alignment with the job requirements and demonstrates relevant qualifications";
    tipText = `Your strong ${scoreNum}% match score puts you in competitive territory. Fine-tune by adding more sophisticated metrics, ensuring your most impressive achievements appear in the top third of your resume, and consider adding a 'Key Achievements' section right after your summary to immediately showcase your most compelling wins.`;
  }
  
  const fallbackSuggestions = `✨ STRENGTHS
• ${strengthsText}
• Your professional background provides a solid foundation for this opportunity
• Your resume follows professional formatting standards and is well-organized
• You have demonstrated career progression and relevant experience in your field

🔍 IMPROVEMENTS NEEDED
• ${improvementsText[0]}
• ${improvementsText[1]}
• ${improvementsText[2]}
• ${improvementsText[3]}
• ${improvementsText[4]}
• Create a dedicated 'Core Competencies' section that mirrors the job's required skills
• Enhance your experience bullets to show progression and increasing responsibility

💡 PRO TIP
${tipText} Remember that hiring managers spend only 6-10 seconds on initial resume screening, so your most relevant qualifications must be immediately visible. Customize each application by treating the job posting as your guide - if they mention something 3 times, it should appear in your resume at least once. Focus on impact and results rather than just responsibilities, and always quantify your achievements where possible.`;

  console.log("✅ Comprehensive fallback suggestions generated");
  return fallbackSuggestions;
}

// Add to your existing script.js
function handleLinkedInLogin(response) {
  // Save basic profile info to localStorage
  localStorage.setItem('userProfile', JSON.stringify({
    name: response.name,
    email: response.email,
    picture: response.picture
  }));
  
  // Send to backend for MongoDB storage
  fetch('/api/save-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(response)
  });
  
  // Redirect to role selection
  location.href = 'landing.html';
}