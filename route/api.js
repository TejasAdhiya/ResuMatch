const express = require('express');
const router = express.Router();
const JobSeeker = require('../models/JobSeeker');
const { calculateSimilarity } = require('../controllers/openaiController');
const { extractText } = require('../util/pdfParser');

router.post('/match-candidates', async (req, res) => {
  const { jobDescription, state } = req.body;

  try {
    // 1. Fetch candidates by state
    const candidates = await JobSeeker.find({ state });

    // 2. Process each candidate
    const matches = await Promise.all(
      candidates.map(async (candidate) => {
        const resumeText = await extractText(candidate.resume);
        const score = await calculateSimilarity(jobDescription, resumeText);
        return {
          name: candidate.originalFileName.replace('.pdf', ''),
          linkedin: candidate.linkedin_url,
          score: Math.round(score * 100),
          resumeText: resumeText.slice(0, 200) + '...', // Preview
        };
      })
    );

    // 3. Sort by score (descending)
    matches.sort((a, b) => b.score - a.score);
    res.json({ success: true, matches });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;