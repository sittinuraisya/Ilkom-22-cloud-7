const mongoose = require("mongoose");

const attendeeSchema = new mongoose.Schema({
  name: String,
  email: String,
  eventId: String,
});

module.exports = mongoose.model("Attendee", attendeeSchema);