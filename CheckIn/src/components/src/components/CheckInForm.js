'use client';

import { useState } from 'react';

export default function CheckInForm() {
  const [nama, setNama] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Nama:', nama);
    console.log('Email:', email);
    alert('Check-in berhasil! (sementara)');
    setNama('');
    setEmail('');
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
        className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700"
      >
        Check In
      </button>
    </form>
  );
}