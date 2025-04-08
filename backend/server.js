require("dotenv").config();
const express = require('express');
const bodyParser = require("body-parser");
const cors = require("cors");
const QRCode = require("qrcode");
const sgMail = require("@sendgrid/mail");
const { v4: uuidv4 } = require("uuid");
const rateLimit = require("express-rate-limit");

const app = express();

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(",") || "*"
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const requiredEnvVars = ["SENDGRID_API_KEY", "SENDER_EMAIL"];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    console.error(`❌ Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
}

sgMail.setApiKey(process.env.SENDGRID_API_KEY);

// Rate limiting configuration
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: "Too many requests from this IP, please try again later"
});

// Data storage (in-memory for development)
const events = new Map();
const attendees = new Map();

// Helper functions
const errorResponse = (res, status, message) => {
  return res.status(status).json({ 
    success: false,
    error: message 
  });
};

const validateEventData = (data) => {
  if (!data.name || !data.date || !data.location) {
    return "Name, date, and location are required";
  }
  if (new Date(data.date) < new Date()) {
    return "Event date cannot be in the past";
  }
  return null;
};

// Endpoint: Create New Event
app.post("/api/events", apiLimiter, async (req, res) => {
  try {
    const validationError = validateEventData(req.body);
    if (validationError) {
      return errorResponse(res, 400, validationError);
    }

    const { name, date, location, description } = req.body;
    const eventId = uuidv4();
    const url = `${process.env.BASE_URL || "http://localhost:3000"}/checkin/${eventId}`;
    
    const qrImage = await QRCode.toDataURL(url);
    
    const newEvent = {
      id: eventId,
      name,
      date,
      location,
      description: description || "",
      qrImage,
      createdAt: new Date().toISOString()
    };

    events.set(eventId, newEvent);
    
    return res.status(201).json({
      success: true,
      data: newEvent
    });

  } catch (err) {
    console.error("Event creation error:", err);
    return errorResponse(res, 500, "Internal server error");
  }
});

// Endpoint: Get Event Details
app.get("/api/events/:eventId", apiLimiter, async (req, res) => {
  try {
    const { eventId } = req.params;
    
    if (!events.has(eventId)) {
      return errorResponse(res, 404, "Event not found");
    }

    const event = events.get(eventId);
    return res.json({
      success: true,
      data: event
    });

  } catch (err) {
    console.error("Get event error:", err);
    return errorResponse(res, 500, "Internal server error");
  }
});

// Endpoint: Check-In Participant
app.post("/api/checkin", apiLimiter, async (req, res) => {
  try {
    const { name, email, eventId } = req.body;

    if (!email || !eventId) {
      return errorResponse(res, 400, "Email and Event ID are required");
    }

    if (!events.has(eventId)) {
      return errorResponse(res, 404, "Event not found");
    }

    const checkInId = uuidv4();
    const checkInData = {
      id: checkInId,
      name: name || "Guest",
      email,
      eventId,
      checkedInAt: new Date().toISOString()
    };

    if (!attendees.has(eventId)) {
      attendees.set(eventId, new Map());
    }
    attendees.get(eventId).set(checkInId, checkInData);

    // Send confirmation email
    const event = events.get(eventId);
    const msg = {
      to: email,
      from: process.env.SENDER_EMAIL,
      subject: `✅ Successfully checked in to: ${event.name}`,
      text: `Hello ${name || "there"}!\n\nYou've successfully checked in to:\n\nEvent: ${event.name}\nDate: ${new Date(event.date).toLocaleString()}\nLocation: ${event.location}`,
      html: `<p>Hello ${name || "there"}!</p>
             <p>You've successfully checked in to:</p>
             <ul>
               <li><strong>Event:</strong> ${event.name}</li>
               <li><strong>Date:</strong> ${new Date(event.date).toLocaleString()}</li>
               <li><strong>Location:</strong> ${event.location}</li>
             </ul>`
    };

    await sgMail.send(msg);

    return res.json({
      success: true,
      message: "Check-in successful!",
      data: {
        checkInId,
        eventDetails: {
          name: event.name,
          date: event.date
        }
      }
    });

  } catch (err) {
    console.error("Check-in error:", err);
    
    // If check-in succeeded but email failed, still return success
    if (err.response && err.response.body) {
      console.error("SendGrid error details:", err.response.body);
      return res.json({
        success: true,
        message: "Check-in completed but email notification failed",
        warning: "Email notification could not be sent"
      });
    }

    return errorResponse(res, 500, "Check-in process failed");
  }
});

// Endpoint: Get Event Attendees
app.get("/api/events/:eventId/attendees", apiLimiter, async (req, res) => {
  try {
    const { eventId } = req.params;
    
    if (!events.has(eventId)) {
      return errorResponse(res, 404, "Event not found");
    }

    const eventAttendees = attendees.get(eventId) || new Map();
    
    return res.json({
      success: true,
      data: {
        event: events.get(eventId),
        attendees: Array.from(eventAttendees.values()),
        totalAttendees: eventAttendees.size
      }
    });

  } catch (err) {
    console.error("Get attendees error:", err);
    return errorResponse(res, 500, "Internal server error");
  }
});

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({
    status: "OK",
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || "development"
  });
});

// 404 handler
app.use((req, res) => {
  errorResponse(res, 404, "Endpoint not found");
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  errorResponse(res, 500, "Internal server error");
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
  console.log(`🛡️ Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(`🌐 Allowed origins: ${process.env.ALLOWED_ORIGINS || "*"}`);
});