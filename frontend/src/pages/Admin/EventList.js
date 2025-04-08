import { useEffect, useState } from "react";
import axios from "axios";

function EventList() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    axios.get("/api/events").then((res) => setEvents(res.data));
  }, []);

  return (
    <div>
      <h2>Daftar Acara</h2>
      {events.map((event) => (
        <div key={event._id}>
          <h3>{event.name}</h3>
          <p>Lokasi: {event.location}</p>
          <img src={event.qrCodeUrl} alt="QR Code" width="100" />
        </div>
      ))}
    </div>
  );
}