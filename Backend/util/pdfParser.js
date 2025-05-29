const fs = require('fs');
const path = require('path'); 
const pdf = require('pdf-parse');

const extractText = async (filePath) => {
  try {
    // If resumePath starts with 'uploads', make it absolute from project root
    let finalPath = filePath;
    if (!path.isAbsolute(finalPath)) {
      finalPath = path.join(__dirname, '..', filePath.replace(/^uploads[\\/]/, 'uploads/'));
    }

    const dataBuffer = fs.readFileSync(finalPath);
    const { text } = await pdf(dataBuffer);
    return text;
  } catch (err) {
    throw new Error(`PDF Extraction Failed: ${err.message}`);
  }
};

module.exports = { extractText };