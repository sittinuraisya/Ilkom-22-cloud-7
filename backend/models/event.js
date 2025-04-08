const mongoose = require("mongoose");

const eventSchema = new mongoose.Schema({
  name: String,
  date: Date,
  location: String,
  description: String,
  createdBy: String, 
  qrCodeUrl: String, // Link/URL QR Code
});

module.exports = mongoose.model("Event", eventSchema);