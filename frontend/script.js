// File upload preview with beautiful display
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

// Auto-resize textarea container (fixed height with scroll)
document.getElementById('jobDescription').addEventListener('input', function() {
  // No auto-resizing needed since we want fixed height with scroll
});

// Main form submission with auto-scroll to results
document.getElementById("uploadForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const btnLoader = document.getElementById("btnLoader");
  const loading = document.getElementById("loading");
  const resultDiv = document.getElementById("result");
  
  // Show loading state
  submitBtn.disabled = true;
  btnText.style.display = "none";
  btnLoader.style.display = "inline";
  loading.style.display = "block";
  
  // Hide previous results
  resultDiv.style.display = "none";
  
  // Form data
  const formData = new FormData();
  formData.append("file", document.getElementById("resume").files[0]);
  formData.append("job_description", document.getElementById("jobDescription").value);

  try {
    const response = await fetch("http://127.0.0.1:8000/api/upload-resume", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Analysis failed. Please try again.");
    const data = await response.json();

    // Display beautiful results
    resultDiv.innerHTML = `
      <h2 id="resultsHeader">Analysis Results</h2>
      
      <div class="result-section">
        <h3>Match Score</h3>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${data.similarity_score}%"></div>
          </div>
          <p class="score-text">Your resume matches <strong>${data.similarity_score}%</strong> of the job requirements</p>
        </div>
      </div>
      
      <div class="result-section">
        <h3>Matched Keywords</h3>
        <p>These keywords from the job description were found in your resume:</p>
        <div class="keyword-container" id="matchedKeywords"></div>
      </div>
      
      <div class="result-section">
        <h3>Missing Keywords</h3>
        <p>Consider adding these important keywords to improve your match:</p>
        <div class="keyword-container" id="missingKeywords"></div>
      </div>
      
      <div class="result-section">
        <h3>Suggestions</h3>
        <div class="suggestions-text" id="suggestions"></div>
      </div>
    `;

    // Populate matched keywords (parrot green)
    const matchedKeywordsContainer = document.getElementById("matchedKeywords");
    if (data.matched_keywords && data.matched_keywords.length > 0) {
      data.matched_keywords.forEach(keyword => {
        const keywordElement = document.createElement('div');
        keywordElement.className = 'keyword matched-keyword';
        keywordElement.textContent = keyword;
        matchedKeywordsContainer.appendChild(keywordElement);
      });
    } else {
      matchedKeywordsContainer.innerHTML = '<p>No keywords matched.</p>';
    }

    // Populate missing keywords (light red)
    const missingKeywordsContainer = document.getElementById("missingKeywords");
    if (data.missing_keywords && data.missing_keywords.length > 0) {
      data.missing_keywords.forEach(keyword => {
        const keywordElement = document.createElement('div');
        keywordElement.className = 'keyword missing-keyword';
        keywordElement.textContent = keyword;
        missingKeywordsContainer.appendChild(keywordElement);
      });
    } else {
      missingKeywordsContainer.innerHTML = '<p>Great job! No important keywords missing.</p>';
    }

    // Typewriter effect for suggestions
    typewriterEffect("suggestions", data.suggestion || "No specific suggestions available.");

    // Celebrate matches with gold-themed confetti
    if (data.similarity_score >= 20) {
      confetti({
        particleCount: Math.min(100, 50 + (data.similarity_score * 3)),
        spread: 70,
        origin: { y: 0.6 },
        colors: ['darkgoldenrod', '#ffd700', '#ffc125'],
        scalar: 0.9
      });
    }

    // Show results
    resultDiv.style.display = "block";
    
    // Smooth scroll to results after short delay
    setTimeout(() => {
      const resultsHeader = document.getElementById("resultsHeader");
      const headerPosition = resultsHeader.getBoundingClientRect().top + window.pageYOffset;
      const scrollStopPosition = headerPosition - 20; // 20px padding from top
      
      window.scrollTo({
        top: scrollStopPosition,
        behavior: 'smooth'
      });
    }, 300);

  } catch (error) {
    alert(error.message);
  } finally {
    submitBtn.disabled = false;
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
    loading.style.display = "none";
  }
});