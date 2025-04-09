'use client';

import { Html5Qrcode } from 'html5-qrcode';
import { useEffect, useRef, useState } from 'react';

export default function QRScanner() {
  const scannerRef = useRef(null);
  const [status, setStatus] = useState('Siap scan...');

  useEffect(() => {
    const qr = new Html5Qrcode('qr-reader');
    const config = { fps: 10, qrbox: 250 };

    qr.start(
      { facingMode: 'environment' },
      config,
      async (decodedText) => {
        setStatus('QR Terdeteksi!');
        try {
          const data = JSON.parse(decodedText); // format QR: {"nama":"Ari","email":"ari@example.com"}
          const res = await fetch('https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: { 'Content-Type': 'application/json' },
          });

          const result = await res.json();
          if (result.result === 'success') {
            alert('Check-in berhasil untuk: ' + data.nama);
          } else {
            alert('Check-in gagal.');
          }
        } catch (err) {
          alert('QR tidak valid!');
        }

        qr.stop().then(() => {
          setStatus('Scan selesai.');
        });
      },
      (err) => {
        console.warn(err);
      }
    );

    return () => {
      qr.stop();
    };
  }, []);

  return (
    <>
      <div id="qr-reader" ref={scannerRef} className="w-full h-64 mb-4" />
      <p className="text-center text-sm text-gray-500">{status}</p>
    </>
  );
}