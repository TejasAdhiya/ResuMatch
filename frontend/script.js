// File upload preview with detailed display
document.getElementById('resume').addEventListener('change', function (e) {
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
document.getElementById("uploadForm").addEventListener("submit", async function (e) {
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

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Analysis failed. Please try again.");
        }
        const data = await response.json();

        // Predefined suggestions
        const suggestions = `
          <p>✨ <strong>Projects:</strong> Consider adding projects to showcase your hands-on experience and technical skills.</p>
          <p>💡 <strong>Certifications:</strong> Adding relevant certifications can boost your credibility and highlight your expertise.</p>
          <p>🔍 <strong>Achievements:</strong> Include quantifiable achievements to make your resume more impactful.</p>
        `;

        // Display the results beautifully
        resultDiv.innerHTML = `
          <h2 id="resultsHeader">Analysis Results</h2>
          
          <div class="result-section">
            <h3>Match Score</h3>
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${data.similarity_score}%"></div>
              </div>
              <p class="score-text">Your resume matches <strong>${data.similarity_score}%</strong> of the job requirements.</p>
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
            <h3>Suggestions for Improvement</h3>
            <div class="suggestions-container">
              ${suggestions}
            </div>
          </div>
        `;

        // Add celebratory confetti if match score is high
        if (data.similarity_score > 15) {
            confetti({
                particleCount: Math.min(100, 50 + (data.similarity_score * 2)),
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#ffd700', '#ff4500', '#00ff7f'],
                scalar: 1.1,
            });
        }

        // Show the results
        resultDiv.style.display = "block";

        // Smooth scroll to the results section
        setTimeout(() => {
            const resultsHeader = document.getElementById("resultsHeader");
            const headerPosition = resultsHeader.getBoundingClientRect().top + window.pageYOffset;
            const scrollStopPosition = headerPosition - 20; // 20px padding from the top

            window.scrollTo({
                top: scrollStopPosition,
                behavior: 'smooth'
            });
        }, 300);

    } catch (error) {
        alert(error.message);
    } finally {
        // Reset the button state
        submitBtn.disabled = false;
        btnText.style.display = "inline";
        btnLoader.style.display = "none";
        loading.style.display = "none";
    }
});
