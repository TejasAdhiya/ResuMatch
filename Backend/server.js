const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();

// Enhanced CORS configuration
app.use(cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5501', 'http://127.0.0.1:5501','http://localhost:5500', 'http://127.0.0.1:5500'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  optionsSuccessStatus: 200 // For legacy browser support
}));
// Add preflight handling
app.options('*', cors());

// Add additional headers to prevent caching issues
app.use((req, res, next) => {
  res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.header('Pragma', 'no-cache');
  res.header('Expires', '0');
  next();
});
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Create uploads directory if it doesn't exist
const uploadsDir = 'uploads';
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
  console.log('Created uploads directory');
}

// Connect to MongoDB with better error handling
mongoose.connect('mongodb://localhost:27017/resumatch', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(() => {
    console.log('✅ Connected to MongoDB - resumatch database');
    console.log('Database URL: mongodb://localhost:27017/resumatch');
  })
  .catch(err => {
    console.error('❌ MongoDB connection error:', err);
    process.exit(1);
  });

// Enhanced file upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    // Create unique filename with timestamp
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const fileExtension = path.extname(file.originalname);
    const baseName = path.basename(file.originalname, fileExtension);
    cb(null, `${baseName}-${uniqueSuffix}${fileExtension}`);
  }
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['.pdf', '.doc', '.docx'];
    const fileExt = path.extname(file.originalname).toLowerCase();
    if (allowedTypes.includes(fileExt)) {
      cb(null, true);
    } else {
      cb(new Error('Only PDF, DOC, and DOCX files are allowed'));
    }
  },
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB limit
  }
});

// Enhanced Database Schema for jobseekers collection
const jobSeekerSchema = new mongoose.Schema({
  resume: { 
    type: String, 
    required: true,
    description: 'File path to uploaded resume' 
  },
  originalFileName: {
    type: String,
    required: true,
    description: 'Original name of uploaded file'
  },
  state: { 
    type: String, 
    required: true,
    trim: true,
    description: 'Selected state for job search'
  },
  linkedin_url: { 
    type: String, 
    required: true,
    trim: true,
    description: 'LinkedIn profile URL'
  },
  fileSize: {
    type: Number,
    description: 'Size of uploaded file in bytes'
  },
  createdAt: { 
    type: Date, 
    default: Date.now,
    description: 'Timestamp when profile was created'
  },
  updatedAt: {
    type: Date,
    default: Date.now,
    description: 'Timestamp when profile was last updated'
  }
});

// Add index for better query performance
jobSeekerSchema.index({ createdAt: -1 });
jobSeekerSchema.index({ state: 1 });

const JobSeeker = mongoose.model('JobSeeker', jobSeekerSchema);

// Enhanced API Endpoint to Save Profile Data to MongoDB
app.post('/api/save-profile', upload.single('file'), async (req, res) => {
  console.log('\n🔄 Processing profile save request...');
  console.log('Request body:', req.body);
  console.log('Uploaded file:', req.file ? {
    originalname: req.file.originalname,
    filename: req.file.filename,
    size: req.file.size,
    mimetype: req.file.mimetype
  } : 'No file uploaded');

  try {
    const { state, linkedin_url } = req.body;
    
    // Enhanced validation
    if (!req.file) {
      console.log('❌ Validation failed: No resume file provided');
      return res.status(400).json({ 
        error: 'Resume file is required',
        details: 'Please upload a PDF, DOC, or DOCX file'
      });
    }
    
    if (!state || state.trim() === '') {
      console.log('❌ Validation failed: No state provided');
      return res.status(400).json({ 
        error: 'State is required',
        details: 'Please select a state for your job search'
      });
    }
    
    if (!linkedin_url || linkedin_url.trim() === '') {
      console.log('❌ Validation failed: No LinkedIn URL provided');
      return res.status(400).json({ 
        error: 'LinkedIn URL is required',
        details: 'Please provide your LinkedIn profile URL'
      });
    }

    // Validate LinkedIn URL format
    const linkedinPattern = /^(https?:\/\/)?www\.linkedin\.com\/in\/[\w\-\.]+\/?$/i;
    if (!linkedinPattern.test(linkedin_url.trim())) {
      console.log('❌ Validation failed: Invalid LinkedIn URL format');
      return res.status(400).json({ 
        error: 'Invalid LinkedIn URL format',
        details: 'Please provide a valid LinkedIn profile URL (e.g., https://www.linkedin.com/in/yourprofile)'
      });
    }

    console.log('✅ Validation passed. Saving profile data...');

    // Create new job seeker record with enhanced data
    const newJobSeeker = new JobSeeker({
      resume: req.file.path,
      originalFileName: req.file.originalname,
      state: state.trim(),
      linkedin_url: linkedin_url.trim(),
      fileSize: req.file.size,
      updatedAt: new Date()
    });
    
    // Save to MongoDB
    const savedProfile = await newJobSeeker.save();
    
    console.log('✅ Profile saved successfully!');
    console.log('Profile ID:', savedProfile._id);
    console.log('File saved at:', savedProfile.resume);
    
    // Send success response
    res.status(201).json({ 
      success: true,
      message: 'Profile saved successfully to database!',
      data: {
        profileId: savedProfile._id,
        state: savedProfile.state,
        linkedin_url: savedProfile.linkedin_url,
        originalFileName: savedProfile.originalFileName,
        fileSize: savedProfile.fileSize,
        createdAt: savedProfile.createdAt
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Error saving profile:', error);
    
    // Clean up uploaded file if there was an error
    if (req.file && fs.existsSync(req.file.path)) {
      try {
        fs.unlinkSync(req.file.path);
        console.log('🧹 Cleaned up uploaded file after error');
      } catch (cleanupError) {
        console.error('❌ Error cleaning up file:', cleanupError);
      }
    }
    
    // Send detailed error response
    res.status(500).json({ 
      error: 'Failed to save profile data to database',
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Enhanced health check endpoint
app.get('/api/health', async (req, res) => {
  try {
    // Test database connection
    const dbStatus = mongoose.connection.readyState === 1 ? 'Connected' : 'Disconnected';
    const profilesCount = await JobSeeker.countDocuments();
    
    res.json({ 
      status: 'MongoDB Server is running successfully',
      database: {
        name: 'resumatch',
        collection: 'jobseekers',
        status: dbStatus,
        totalProfiles: profilesCount
      },
      server: {
        port: PORT,
        nodeVersion: process.version,
        uptime: process.uptime()
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Health check error:', error);
    res.status(500).json({
      status: 'Error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Enhanced endpoint to get all saved profiles
app.get('/api/profiles', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    const skip = parseInt(req.query.skip) || 0;
    
    const profiles = await JobSeeker.find()
      .sort({ createdAt: -1 })
      .limit(limit)
      .skip(skip);
      
    const totalCount = await JobSeeker.countDocuments();
    
    res.json({
      success: true,
      pagination: {
        total: totalCount,
        limit: limit,
        skip: skip,
        hasMore: (skip + limit) < totalCount
      },
      profiles: profiles.map(profile => ({
        id: profile._id,
        state: profile.state,
        linkedin_url: profile.linkedin_url,
        originalFileName: profile.originalFileName,
        fileSize: profile.fileSize,
        created_at: profile.createdAt,
        updated_at: profile.updatedAt
      }))
    });
  } catch (error) {
    console.error('Error fetching profiles:', error);
    res.status(500).json({ 
      error: 'Failed to fetch profiles',
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Delete a specific profile (useful for testing)
app.delete('/api/profiles/:id', async (req, res) => {
  try {
    const profileId = req.params.id;
    const profile = await JobSeeker.findById(profileId);
    
    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' });
    }
    
    // Delete the file if it exists
    if (fs.existsSync(profile.resume)) {
      fs.unlinkSync(profile.resume);
      console.log('Deleted file:', profile.resume);
    }
    
    // Delete from database
    await JobSeeker.findByIdAndDelete(profileId);
    
    res.json({
      success: true,
      message: 'Profile deleted successfully',
      deletedProfile: {
        id: profile._id,
        originalFileName: profile.originalFileName
      }
    });
  } catch (error) {
    console.error('Error deleting profile:', error);
    res.status(500).json({ 
      error: 'Failed to delete profile',
      details: error.message 
    });
  }
});

// Enhanced error handling middleware
app.use((error, req, res, next) => {
  console.error('Server Error:', error);
  
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ 
        error: 'File too large',
        details: 'Maximum file size is 5MB. Please choose a smaller file.'
      });
    }
    if (error.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({ 
        error: 'Unexpected file field',
        details: 'Please use the correct file upload field.'
      });
    }
  }
  
  res.status(500).json({ 
    error: 'Internal server error',
    details: error.message,
    timestamp: new Date().toISOString()
  });
});

// Handle 404 for unknown routes
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    availableEndpoints: [
      'POST /api/save-profile',
      'GET /api/health',
      'GET /api/profiles',
      'DELETE /api/profiles/:id'
    ]
  });
});

// Start server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log('\n🚀 MongoDB Server started successfully!');
  console.log(`📡 Server running on http://localhost:${PORT}`);
  console.log('\n📋 Available endpoints:');
  console.log(`   POST http://localhost:${PORT}/api/save-profile (saves user data to MongoDB)`);
  console.log(`   GET  http://localhost:${PORT}/api/health (server health check)`);
  console.log(`   GET  http://localhost:${PORT}/api/profiles (view saved profiles)`);
  console.log(`   DELETE http://localhost:${PORT}/api/profiles/:id (delete specific profile)`);
  console.log('\n⚠️  Important Notes:');
  console.log('   • Job fetching is handled by your Python Flask server on port 5000');
  console.log('   • Make sure your Python Flask server is also running on port 5000!');
  console.log('   • MongoDB should be running on mongodb://localhost:27017');
  console.log('\n' + '='.repeat(60));
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down server...');
  try {
    await mongoose.connection.close();
    console.log('✅ MongoDB connection closed');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
});