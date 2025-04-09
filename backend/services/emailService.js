const sgMail = require("@sendgrid/mail");
sgMail.setApiKey(process.env.SENDGRID_API_KEY);

function sendConfirmationEmail(email, eventName) {
  const msg = {
    to: email,
    from: "admin@yourapp.com", // Ganti dengan email yang diverifikasi di SendGrid
    subject: `Berhasil Check-in di ${eventName}`,
    text: "Terima kasih telah hadir!",
  };
  sgMail.send(msg)
    .then(() => console.log("Email sent"))
    .catch((error) => console.error("Error sending email:", error));
}

module.exports = { sendConfirmationEmail };
