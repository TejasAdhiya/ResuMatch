const OpenAI = require('openai');
const cosineSimilarity = require('compute-cosine-similarity');
const { extractText } = require('../util/pdfParser');

const openai = new OpenAI({
  apiKey: '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',
});

const calculateSimilarity = async (jobDesc, resumeText) => {
  try {
    // Get embeddings
    const embeddingRes = await openai.embeddings.create({
      input: [jobDesc, resumeText],
      model: 'text-embedding-3-small',
    });

    // Extract vectors
    const [vec1, vec2] = embeddingRes.data.map(item => item.embedding);

    // Calculate similarity
    return cosineSimilarity(vec1, vec2);
  } catch (err) {
    throw new Error(`OpenAI Error: ${err.message}`);
  }
};

module.exports = { calculateSimilarity };