const express = require('express');
const router = express.Router();
const {
  getEvents,
  getEvent,
  createEvent,
  updateEvent,
  deleteEvent,
  getEventAttendees
} = require('../controllers/eventController');
const { protect, authorize } = require('../middleware/auth');

// Public routes
router.get('/', getEvents);
router.get('/:id', getEvent);

// Protected routes (require authentication)
router.use(protect);

router.post('/', authorize('admin', 'organizer'), createEvent);
router.put('/:id', authorize('admin', 'organizer'), updateEvent);
router.delete('/:id', authorize('admin', 'organizer'), deleteEvent);
router.get('/:id/attendees', authorize('admin', 'organizer'), getEventAttendees);

module.exports = router;
