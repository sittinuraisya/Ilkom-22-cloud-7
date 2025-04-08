const express = require("express");
const router = express.Router();
const Event = require("../models/event");
const { authenticateAdmin } = require("../middleware/auth");
const QRCode = require("qrcode");

// POST /api/events - Create new event (Admin only)
router.post("/", authenticateAdmin, async (req, res) => {
  try {
    const { name, date, location, description } = req.body;
    const createdBy = req.user.email; // From authenticated admin

    // Generate QR Code
    const qrCodeUrl = await QRCode.toDataURL(
      `https://yourapp.com/checkin/${encodeURIComponent(name)}`
    );

    // Save to database
    const event = new Event({
      name,
      date,
      location,
      description,
      createdBy,
      qrCodeUrl,
    });

    await event.save();
    res.status(201).json(event);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to create event" });
  }
});

// GET /api/events - Get all events
router.get("/", async (req, res) => {
  try {
    const events = await Event.find();
    res.json(events);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch events" });
  }
});

module.exports = router;