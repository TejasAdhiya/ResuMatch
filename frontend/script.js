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

    // Display beautiful results with perfect formatting
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
        <div class="keyword-container" id="matchedKeywords">
          ${data.matched_keywords.map(kw => `<span class="keyword matched-keyword">${kw}</span>`).join('') || '<p>No keywords matched.</p>'}
        </div>
      </div>
      
      <div class="result-section">
        <h3>Missing Keywords</h3>
        <p>Consider adding these important keywords to improve your match:</p>
        <div class="keyword-container" id="missingKeywords">
          ${data.missing_keywords.map(kw => `<span class="keyword missing-keyword">${kw}</span>`).join('') || '<p>Great job! No important keywords missing.</p>'}
        </div>
      </div>
      
      <div class="result-section">
        <h3>Optimization Suggestions</h3>
        <div class="suggestions-container">
          ${formatSuggestions(data.suggestion)}
        </div>
      </div>
    `;

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

// Format suggestions with perfect line breaks and structure
function formatSuggestions(text) {
  if (!text) return '<p class="no-suggestions">No suggestions available</p>';
  
  // Process each line with proper formatting
  const lines = text.split('\n');
  let html = '';
  let currentList = null;

  lines.forEach(line => {
    if (line.startsWith('✨ STRENGTHS')) {
      html += `<div class="suggestion-section strength-section">
                <div class="section-header strength-header">
                  <i class="fas fa-check-circle"></i> ${line.substring(2)}
                </div>
                <ul class="suggestion-list">`;
      currentList = 'strength';
    } 
    else if (line.startsWith('🔍 IMPROVEMENTS')) {
      html += `</ul></div>
              <div class="suggestion-section improvement-section">
                <div class="section-header improvement-header">
                  <i class="fas fa-search-plus"></i> ${line.substring(2)}
                </div>
                <ul class="suggestion-list">`;
      currentList = 'improvement';
    }
    else if (line.startsWith('💡 PRO TIP')) {
      html += `</ul></div>
              <div class="suggestion-section tip-section">
                <div class="section-header tip-header">
                  <i class="fas fa-lightbulb"></i> ${line.substring(2)}
                </div>
                <div class="tip-content">`;
      currentList = 'tip';
    }
    else if (line.startsWith('•')) {
      const content = line.substring(1).trim();
      if (currentList === 'tip') {
        html += `<p>${content}</p>`;
      } else {
        html += `<li>${content}</li>`;
      }
    }
    else if (line.trim() === '') {
      // Skip empty lines
    }
    else {
      // For regular text in tip section
      if (currentList === 'tip') {
        html += `<p>${line}</p>`;
      } else if (currentList) {
        html += `<li>${line}</li>`;
      }
    }
  });

  // Close any open tags
  if (currentList === 'strength' || currentList === 'improvement') {
    html += '</ul></div>';
  } else if (currentList === 'tip') {
    html += '</div></div>';
  }

  return html;
}