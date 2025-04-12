const express = require('express');
const router = express.Router();
const {
  registerForEvent,
  checkInToEvent,
  getMyRegistrations,
  cancelRegistration
} = require('../controllers/attendeeController');
const { protect } = require('../middleware/auth');

// Apply authentication middleware to all routes
router.use(protect);

// User registration management
router.post('/register/:eventId', registerForEvent);
router.get('/my-registrations', getMyRegistrations);
router.delete('/cancel/:registrationId', cancelRegistration);

// Check-in functionality
router.put('/checkin/:registrationId', checkInToEvent);

module.exports = router;
