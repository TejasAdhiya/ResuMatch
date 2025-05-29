const express = require('express');
const router = express.Router();
const JobSeeker = require('../models/JobSeeker');
const { calculateSimilarity } = require('../controllers/openaiController');
const { extractText } = require('../util/pdfParser');

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
          return {
            name: candidate.originalFileName.replace('.pdf', ''),
            linkedin: candidate.linkedin_url,
            score: Math.round(score * 100),
            resumeText: resumeText.slice(0, 200) + '...', // Preview
            resumeUrl: candidate.resume
              ? `/uploads/${candidate.resume.replace(/^uploads[\\/]/, '')}`
              : null
          };
        } catch (innerErr) {
          console.error('Error processing candidate:', candidate.originalFileName, innerErr);
          return null; // or handle as you wish
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