const nodemailer = require('nodemailer');
const ErrorResponse = require('./errorResponse');

// Create reusable transporter object using SMTP transport
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: process.env.SMTP_SECURE === 'true', // true for 465, false for other ports
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
});

// Verify connection configuration
transporter.verify((error) => {
  if (error) {
    console.error('SMTP connection error:', error);
  } else {
    console.log('Server is ready to send emails');
  }
});

// Send email function
const sendEmail = async ({ email, subject, message }) => {
  try {
    const mailOptions = {
      from: `"Event Attendance" <${process.env.SMTP_FROM}>`,
      to: email,
      subject,
      text: message,
      html: `<div>${message}</div>` // Basic HTML version
    };

    await transporter.sendMail(mailOptions);
  } catch (err) {
    console.error('Email send error:', err);
    throw new ErrorResponse('Email could not be sent', 500);
  }
};

module.exports = sendEmail;
