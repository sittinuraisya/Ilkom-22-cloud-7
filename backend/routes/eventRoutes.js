const express = require("express");
const router = express.Router();
const Event = require("../models/event");
const QRCode = require("qrcode");

// Buat Acara Baru
router.post("/", async (req, res) => {
  try {
    const { name, date, location, description, createdBy } = req.body;

    // Generate QR Code
    const qrCodeUrl = await QRCode.toDataURL(
      `http://localhost:3000/checkin?event=${name}`
    );

    // Simpan ke database
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
    res.status(500).json({ error: "Gagal membuat acara" });
  }
});

// Ambil Daftar Acara
router.get("/", async (req, res) => {
  try {
    const events = await Event.find();
    res.json(events);
  } catch (err) {
    res.status(500).json({ error: "Gagal mengambil data" });
  }
});

module.exports = router;