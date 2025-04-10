import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function CreateEvent() {
  const [eventData, setEventData] = useState({
    name: "",
    date: "",
    location: "",
    description: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      const res = await axios.post("/api/events", {
        ...eventData,
        createdBy: localStorage.getItem("adminEmail") || "admin@kampus.com",
      });
      
      alert(`Acara "${res.data.event.name}" berhasil dibuat!`);
      navigate("/admin/events"); // Redirect to events list
    } catch (err) {
      setError(err.response?.data?.message || "Gagal membuat acara");
      console.error("Error creating event:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEventData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="create-event-form">
      <h2>Buat Acara Baru</h2>
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Nama Acara</label>
          <input
            name="name"
            placeholder="Contoh: Seminar Teknologi"
            value={eventData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Tanggal dan Waktu</label>
          <input
            type="datetime-local"
            name="date"
            value={eventData.date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Lokasi</label>
          <input
            name="location"
            placeholder="Contoh: Gedung A Lantai 3"
            value={eventData.location}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Deskripsi</label>
          <textarea
            name="description"
            placeholder="Deskripsi acara..."
            value={eventData.description}
            onChange={handleChange}
            rows={3}
          />
        </div>

        <button 
          type="submit" 
          disabled={isLoading}
          className="submit-button"
        >
          {isLoading ? "Memproses..." : "Buat Acara"}
        </button>
      </form>
    </div>
  );
}

export default CreateEvent;