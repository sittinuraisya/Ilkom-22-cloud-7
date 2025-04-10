'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useSession, signIn, signOut } from 'next-auth/react';

function formatDateTime(datetime) {
  const date = new Date(datetime);
  return `${date.getHours()}:00`;
}

export default function AdminPage() {
  const { data: session, status } = useSession();
  const [peserta, setPeserta] = useState([]);
  const [statistik, setStatistik] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') signIn();
    if (status === 'authenticated') {
      fetch(process.env.NEXT_PUBLIC_SCRIPT_URL)
        .then(res => res.json())
        .then(data => {
          if (data.result === 'success') {
            setPeserta(data.data);
            const countPerHour = {};
            data.data.forEach(item => {
              const jam = formatDateTime(item['Waktu Check-In']);
              countPerHour[jam] = (countPerHour[jam] || 0) + 1;
            });
            const chartData = Object.keys(countPerHour).map(jam => ({
              waktu: jam,
              jumlah: countPerHour[jam]
            }));
            setStatistik(chartData);
          }
        })
        .finally(() => setLoading(false));
    }
  }, [status]);

  if (status === 'loading' || loading) return <p>Memuat...</p>;
  if (!session) return null;

  return (
    <main className="p-6 bg-gray-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard Kehadiran</h1>
        <button
          onClick={() => signOut()}
          className="px-4 py-2 bg-red-500 text-white rounded-xl"
        >
          Logout
        </button>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-md mb-8">
        <h2 className="text-lg font-semibold mb-4">Statistik Check-In per Jam</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={statistik}>
            <XAxis dataKey="waktu" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="jumlah" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-lg font-semibold mb-4">Daftar Peserta Check-In</h2>
        <table className="w-full">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">Nama</th>
              <th className="p-2">Email</th>
              <th className="p-2">Waktu</th>
            </tr>
          </thead>
          <tbody>
            {peserta.map((item, i) => (
              <tr key={i} className="border-b">
                <td className="p-2">{item['Nama']}</td>
                <td className="p-2">{item['Email']}</td>
                <td className="p-2">{new Date(item['Waktu Check-In']).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}