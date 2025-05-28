const fs = require('fs');
const path = require('path'); 
const pdf = require('pdf-parse');

const extractText = async (filePath) => {
  try {
    // Normalize path and prepend 'Backend/' if not already present
    const normalizedPath = path.normalize(filePath);
    const finalPath = normalizedPath.includes('Backend') 
      ? normalizedPath 
      : path.join('Backend', normalizedPath);

    const dataBuffer = fs.readFileSync(finalPath);
    const { text } = await pdf(dataBuffer);
    return text;
  } catch (err) {
    throw new Error(`PDF Extraction Failed: ${err.message}`);
  }
};

module.exports = { extractText };