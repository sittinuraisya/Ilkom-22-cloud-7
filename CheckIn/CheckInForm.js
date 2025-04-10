'use client';
import { useState } from 'react';

export default function CheckInForm() {
  const [nama, setNama] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const endpoint = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec'; // ganti dengan URL kamu

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        body: JSON.stringify({ nama, email }),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await res.json();
      if (result.result === 'success') {
        alert('Check-in berhasil!');
        setNama('');
        setEmail('');
      } else {
        alert('Gagal check-in!');
      }
    } catch (err) {
      console.error(err);
      alert('Terjadi kesalahan.');
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Nama</label>
        <input
          type="text"
          value={nama}
          onChange={(e) => setNama(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded-xl"
        />
      </div>
      <div>
        <label className="block text-sm font-medium">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded-xl"
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700"
      >
        {loading ? 'Mengirim...' : 'Check In'}
      </button>
    </form>
  );
}
