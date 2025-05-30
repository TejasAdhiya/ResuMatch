const BACKEND_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('resume-files');
    const jobDescriptionInput = document.getElementById('job-description');
    const analyzeButton = document.getElementById('analyze-button');
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const fileList = document.getElementById('file-list');

    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        
        if (files.length > 10) {
            alert('Maximum 10 resumes allowed');
            fileInput.value = '';
            return;
        }

        // Clear previous file list
        fileList.innerHTML = '';

        // Display selected files
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div>
                    <i class="fas fa-file-pdf"></i>
                    <span>${file.name}</span>
                </div>
                <button type="button" onclick="removeFile(${index})" class="btn-secondary">
                    <i class="fas fa-times"></i>
                </button>
            `;
            fileList.appendChild(fileItem);
        });
    });

    // Function to remove a file
    window.removeFile = function(index) {
        const dt = new DataTransfer();
        const files = Array.from(fileInput.files);
        files.splice(index, 1);
        files.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        
        // Trigger change event to update file list
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    };

    analyzeButton.addEventListener('click', async function() {
        const files = fileInput.files;
        const jobDescription = jobDescriptionInput.value.trim();

        if (files.length === 0) {
            alert('Please select at least one resume file');
            return;
        }

        if (files.length > 10) {
            alert('Maximum 10 resumes allowed');
            return;
        }

        if (!jobDescription) {
            alert('Please enter a job description');
            return;
        }

        // Show loading spinner
        loadingSpinner.style.display = 'block';
        resultsContainer.innerHTML = '';

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        formData.append('job_description', jobDescription);

        try {
            const response = await fetch(`${BACKEND_URL}/api/analyze-bulk`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Analysis failed');
            }

            const results = await response.json();
            displayResults(results);
        } catch (error) {
            alert('Error analyzing resumes: ' + error.message);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    function parseAnalysis(analysis) {
        // Default values
        let summary = '';
        let strengths = [];
        let weaknesses = [];

        if (!analysis || typeof analysis !== 'string') {
            return { summary: '', strengths: [], weaknesses: [] };
        }

        // Try to extract using known keywords
        // Example format:
        // Score: 85 Analysis: ... Key strengths: ... Key weaknesses: ...
        let main = analysis;
        let scoreMatch = main.match(/^Score:\s*\d+/i);
        if (scoreMatch) {
            main = main.replace(scoreMatch[0], '').trim();
        }

        // Extract Key Strengths and Weaknesses
        let strengthsMatch = main.match(/Key strengths?:[\s\S]*?(?=Key weaknesses?:|$)/i);
        let weaknessesMatch = main.match(/Key weaknesses?:[\s\S]*$/i);

        if (strengthsMatch) {
            let strengthsText = strengthsMatch[0].replace(/Key strengths?:/i, '').trim();
            strengths = strengthsText.split(/[-•\n]/).map(s => s.trim()).filter(s => s.length > 2);
            main = main.replace(strengthsMatch[0], '').trim();
        }
        if (weaknessesMatch) {
            let weaknessesText = weaknessesMatch[0].replace(/Key weaknesses?:/i, '').trim();
            weaknesses = weaknessesText.split(/[-•\n]/).map(s => s.trim()).filter(s => s.length > 2);
            main = main.replace(weaknessesMatch[0], '').trim();
        }

        // The remaining main is the summary/brief analysis
        summary = main.replace(/^Analysis:/i, '').trim();
        // Make summary brief (first 2 sentences)
        if (summary.split('. ').length > 2) {
            summary = summary.split('. ').slice(0, 2).join('. ') + '.';
        }

        return { summary, strengths, weaknesses };
    }

    function getScoreColor(score) {
        if (score >= 70) return '#27ae60'; // green
        if (score < 20) return '#e74c3c'; // red
        return '#f39c12'; // orange
    }

    function displayResults(results) {
        resultsContainer.innerHTML = '';
        
        results.forEach((result, index) => {
            const { summary, strengths, weaknesses } = parseAnalysis(result.analysis);
            const scoreColor = getScoreColor(result.score);
            const resultCard = document.createElement('div');
            resultCard.className = 'result-card';
            resultCard.style.boxShadow = '0 4px 24px rgba(0,0,0,0.18)';
            resultCard.style.marginBottom = '32px';
            resultCard.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 10px;">
                    <span style="font-size: 2rem; font-weight: 800; color: #ffd700; letter-spacing: 1px;">${result.name || 'No Name'}</span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: ${scoreColor}; background: rgba(0,0,0,0.08); padding: 8px 24px; border-radius: 24px; min-width: 120px; text-align: center;">
                        ${result.score}%
                    </span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <i class="fas fa-envelope" style="color: #4cc9f0; font-size: 1.2rem; margin-right: 8px;"></i>
                    <span style="font-size: 1.15rem; font-weight: 600; color: #fff; letter-spacing: 0.5px;">${result.email || 'No Email Found'}</span>
                </div>
                <div class="analysis" style="background: #29261a; border-radius: 12px; padding: 22px 24px 18px 24px; margin: 18px 0 18px 0;">
                    <h4 style="font-size: 1.1rem; color: #ffd700; margin-bottom: 10px; font-weight: 700;">Brief Analysis:</h4>
                    <p style="margin-bottom: 18px; color: #f0e6c8; font-size: 1.05rem;">${summary || 'No summary available.'}</p>
                    <div style="display: flex; gap: 40px; flex-wrap: wrap;">
                        <div style="min-width: 200px;">
                            <strong style="color: #27ae60; font-size: 1.05rem;"><i class="fas fa-check-circle" style="margin-right: 6px;"></i>Key Strengths:</strong>
                            <ul style="margin: 10px 0 0 18px; padding: 0; color: #b6f7c2; font-size: 1rem;">
                                ${strengths.length > 0 ? strengths.map(s => `<li>${s}</li>`).join('') : '<li>Not specified</li>'}
                            </ul>
                        </div>
                        <div style="min-width: 200px;">
                            <strong style="color: #e74c3c; font-size: 1.05rem;"><i class="fas fa-times-circle" style="margin-right: 6px;"></i>Key Weaknesses:</strong>
                            <ul style="margin: 10px 0 0 18px; padding: 0; color: #f7b6b6; font-size: 1rem;">
                                ${weaknesses.length > 0 ? weaknesses.map(w => `<li>${w}</li>`).join('') : '<li>Not specified</li>'}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="actions" style="margin-top: 18px;">
                    <button onclick="sendEmail('acceptance', '${result.email}', '${result.name}')" class="accept-btn">
                        Send Acceptance Email
                    </button>
                    <button onclick="sendEmail('rejection', '${result.email}', '${result.name}')" class="reject-btn">
                        Send Rejection Email
                    </button>
                </div>
            `;
            resultsContainer.appendChild(resultCard);
        });
    }
});

async function sendEmail(type, email, name) {
    let rejectionReason = '';
    
    if (type === 'rejection') {
        // Find the result card for this candidate
        const resultCards = document.querySelectorAll('.result-card');
        for (const card of resultCards) {
            const nameElement = card.querySelector('span[style*="font-size: 2rem"]');
            if (nameElement && nameElement.textContent.trim() === name) {
                // Get the second ul (weaknesses)
                const weaknessesList = card.querySelectorAll('.analysis ul')[1];
                if (weaknessesList) {
                    const weaknesses = Array.from(weaknessesList.querySelectorAll('li'))
                        .map(li => li.textContent.trim())
                        .filter(text => text !== 'Not specified');
                    rejectionReason = weaknesses.join('. ');
                }
                break;
            }
        }
        
        if (!rejectionReason) {
            alert('Could not find rejection reasons. Please try again.');
            return;
        }
    }

    const formData = new FormData();
    formData.append('email_type', type);
    formData.append('recipient_email', email);
    formData.append('candidate_name', name);
    if (type === 'rejection') {
        formData.append('rejection_reason', rejectionReason);
    }

    try {
        const response = await fetch(`${BACKEND_URL}/api/send-email`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Failed to send email');
        }

        const result = await response.json();
        alert('Email sent successfully!');
    } catch (error) {
        alert('Error sending email: ' + error.message);
    }
} 