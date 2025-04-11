const mongoose = require('mongoose');

const AttendeeSchema = new mongoose.Schema({
  event: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Event',
    required: true
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  checkInTime: {
    type: Date,
    default: Date.now
  },
  status: {
    type: String,
    enum: ['registered', 'checked-in', 'cancelled'],
    default: 'registered'
  },
  additionalInfo: {
    type: mongoose.Schema.Types.Mixed
  }
});

// Prevent duplicate registrations
AttendeeSchema.index({ event: 1, user: 1 }, { unique: true });

module.exports = mongoose.model('Attendee', AttendeeSchema);
