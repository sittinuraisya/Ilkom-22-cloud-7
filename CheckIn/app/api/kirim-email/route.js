import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';
import QRCode from 'qrcode';

export async function POST(req) {
  const { email, nama, id } = await req.json();

  try {
    // Generate QR sebagai base64 image
    const qrData = `https://yourdomain.com/checkin?id=${id}`;
    const qrImage = await QRCode.toDataURL(qrData);

    // Setup transporter SMTP (contoh pakai Gmail)
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.EMAIL_SENDER,
        pass: process.env.EMAIL_PASS
      }
    });

    const mailOptions = {
      from: `"Panitia Acara" <${process.env.EMAIL_SENDER}>`,
      to: email,
      subject: `Tiket QR Check-In: ${nama}`,
      html: `
        <p>Halo ${nama},</p>
        <p>Berikut ini adalah tiket QR kamu untuk check-in acara:</p>
        <img src="${qrImage}" alt="QR Code" />
        <p>Sampai jumpa di lokasi!</p>
      `
    };

    await transporter.sendMail(mailOptions);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}