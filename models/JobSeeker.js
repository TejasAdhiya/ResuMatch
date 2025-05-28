const mongoose = require('mongoose');

const JobSeekerSchema = new mongoose.Schema({
  resume: { type: String, required: true },
  originalFileName: { type: String, required: true },
  state: { type: String, required: true },
  linkedin_url: { type: String, required: true },
  filesize: { type: Number },
}, { 
  timestamps: true,
  collection: "jobseekers" // Force use of this collection
});

module.exports = mongoose.model('JobSeeker', JobSeekerSchema);