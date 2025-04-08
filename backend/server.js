require("dotenv").config(); // Load .env
const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
const QRCode = require("qrcode");
const sgMail = require("@sendgrid/mail");

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Set API key SendGrid
sgMail.setApiKey(process.env.SENDGRID_API_KEY);

// Endpoint: Generate QR Code
app.get("/generate-qr", async (req, res) => {
  const eventId = req.query.eventId || "12345"; // Bisa dynamic
  const url = `https://yourapp.com/checkin/${eventId}`;
  try {
    const qrImage = await QRCode.toDataURL(url);
    res.json({ qrImage });
  } catch (err) {
    res.status(500).json({ error: "QR generation failed" });
  }
});

// Endpoint: Check-In Peserta
app.post("/checkin", async (req, res) => {
  const { name, email, eventId } = req.body;

  if (!email || !eventId) {
    return res.status(400).json({ error: "Email dan Event ID wajib diisi" });
  }

  // Di sini kamu bisa simpan ke DB (jika pakai MongoDB/Firebase)

  // Kirim email konfirmasi
  const msg = {
    to: email,
    from: "admin@yourapp.com", // Harus email terverifikasi di SendGrid
    subject: `Berhasil Check-in di Event ${eventId}`,
    text: `Halo ${name},\n\nTerima kasih telah hadir pada event dengan ID: ${eventId}.`,
  };

  try {
    await sgMail.send(msg);
    res.json({ message: "Check-in berhasil & email dikirim!" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Check-in berhasil tapi gagal kirim email." });
  }
});

// Jalankan server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`));
