import CheckInForm from '@/components/CheckInForm';

export default function CheckInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4 text-center">Check-In Kehadiran</h1>
        <CheckInForm />
      </div>
    </main>
  );
}