import { useState } from "react";
import axios from "axios";

function CreateEvent() {
  const [eventData, setEventData] = useState({
    name: "",
    date: "",
    location: "",
    description: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await axios.post("/api/events", {
      ...eventData,
      createdBy: "admin@kampus.com", // Ganti dengan email admin yang login
    });
    alert(`Acara "${res.data.event.name}" berhasil dibuat!`);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        placeholder="Nama Acara"
        value={eventData.name}
        onChange={(e) => setEventData({ ...eventData, name: e.target.value })}
      />
      <input
        type="datetime-local"
        value={eventData.date}
        onChange={(e) => setEventData({ ...eventData, date: e.target.value })}
      />
      <button type="submit">Buat Acara</button>
    </form>
  );
}