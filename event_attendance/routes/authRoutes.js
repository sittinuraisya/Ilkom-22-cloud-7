const express = require('express');
const router = express.Router();
const {
  register,
  login,
  verifyEmail,
  getMe
} = require('../controllers/authController');
const { protect } = require('../middleware/auth');

// Public routes
router.post('/register', register);
router.post('/login', login);
router.get('/verify/:verificationToken', verifyEmail);

// Protected routes
router.get('/me', protect, getMe);

module.exports = router;
