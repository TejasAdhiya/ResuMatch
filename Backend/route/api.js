const express = require('express');
const router = express.Router();
const JobSeeker = require('../models/JobSeeker');
const { calculateSimilarity } = require('../controllers/openaiController');
const { extractText } = require('../util/pdfParser');

// Extracts the likely job title from a block of text
function extractTitle(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  // Look for a line with common job title words
  const titleWords = ['developer','designer','engineer','manager','lead','architect','consultant','specialist','administrator','programmer','scientist','tester','qa','devops','product','project','analyst'];
  for (const line of lines) {
    for (const word of titleWords) {
      if (line.toLowerCase().includes(word)) {
        return line;
      }
    }
  }
  // Fallback: first non-empty line
  return lines[0] || '';
}

router.post('/match-candidates', async (req, res) => {
  const { jobDescription, state } = req.body;
  console.log('Received request:', { jobDescription, state });

  try {
    // 1. Fetch candidates by state
    const candidates = await JobSeeker.find({ state });
    console.log('Candidates found:', candidates.length);

    // 2. Process each candidate
    const matches = await Promise.all(
      candidates.map(async (candidate) => {
        try {
          console.log('Processing candidate:', candidate.originalFileName);
          const resumeText = await extractText(candidate.resume);
          const score = await calculateSimilarity(jobDescription, resumeText);

          // Name extraction logic (keep as is)
          let name = 'Not found';
          const lines = resumeText.split('\n').map(l => l.trim()).filter(Boolean);
          const sectionHeaders = [
            'Professional Summary', 'Technical Skills', 'Skills', 'Summary', 'Objective',
            'Experience', 'Work Experience', 'Education', 'Projects', 'Contact', 'Profile'
          ];
          const nameLine = lines.find(line => /^name[:\-]/i.test(line));
          if (nameLine) {
            name = nameLine.replace(/^name[:\-]\s*/i, '');
          } else {
            const likelyName = lines.find(line => {
              if (sectionHeaders.some(header => line.toLowerCase().includes(header.toLowerCase()))) return false;
              const words = line.split(/\s+/);
              return (
                words.length >= 2 &&
                words[0][0] === words[0][0].toUpperCase() &&
                words[1][0] === words[1][0].toUpperCase() &&
                /^[A-Za-z]+$/.test(words[0]) &&
                /^[A-Za-z]+$/.test(words[1])
              );
            });
            if (likelyName) {
              name = likelyName;
            } else {
              const notContact = lines.find(line =>
                !sectionHeaders.some(header => line.toLowerCase().includes(header.toLowerCase())) &&
                !line.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/) &&
                !line.match(/(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4,}/)
              );
              if (notContact) name = notContact;
              else if (lines.length > 0) name = lines[0];
            }
          }

          // Email and phone extraction
          const emailMatch = resumeText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/i);
          const phoneMatch = resumeText.match(/(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4,}/);

          // Keyword extraction
          function extractKeywords(text) {
            const keywords = ['developer','designer','engineer','manager','lead','architect','consultant','specialist','administrator','programmer','scientist','tester','qa','devops','product','project','react','angular','vue','javascript','python','java','c++','ui','ux','frontend','backend','fullstack','analyst'];
            const found = [];
            const lower = text.toLowerCase();
            for (const word of keywords) {
              if (lower.includes(word)) found.push(word);
            }
            return found;
          }

          // Title and keyword logic
          const jobTitle = extractTitle(jobDescription).toLowerCase();
          const resumeTitle = extractTitle(resumeText).toLowerCase();
          const jobKeywords = extractKeywords(jobDescription);
          const resumeKeywords = extractKeywords(resumeText);

          // Calculate base similarity
          let matchScore = Math.round(score * 100);

          // Boost if titles are similar or at least 2 keywords overlap
          const titleSimilar = jobTitle && resumeTitle && (
            jobTitle.includes(resumeTitle) || resumeTitle.includes(jobTitle)
          );
          const keywordOverlap = jobKeywords.filter(k => resumeKeywords.includes(k));
          if (titleSimilar || keywordOverlap.length >= 2) {
            matchScore = Math.min(100, matchScore + 20); // boost but cap at 100
          }

          // Penalize if no overlap at all
          if (keywordOverlap.length === 0 && !titleSimilar) {
            matchScore = 0;
          }

          if (matchScore >= 30) {
            return {
              name,
              email: emailMatch ? emailMatch[0] : 'Not found',
              contact: phoneMatch ? phoneMatch[0] : 'Not found',
              linkedin: candidate.linkedin_url,
              score: matchScore,
              resumeText: resumeText.slice(0, 200) + '...', // Preview
              resumeUrl: candidate.resume
                ? `/uploads/${candidate.resume.replace(/^uploads[\\/]/, '')}`
                : null
            };
          }
        } catch (innerErr) {
          console.error('Error processing candidate:', candidate.originalFileName, innerErr);
          return null;
        }
      })
    );

    // Remove any nulls if a candidate failed
    const filteredMatches = matches.filter(Boolean);

    // 3. Sort by score (descending)
    filteredMatches.sort((a, b) => b.score - a.score);
    console.log('Returning matches:', filteredMatches.length);
    res.json({ success: true, matches: filteredMatches });
  } catch (err) {
    console.error('Error in /match-candidates:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;