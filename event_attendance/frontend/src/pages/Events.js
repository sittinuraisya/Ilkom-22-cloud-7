import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from '../axiosInstance';
import { toast } from 'react-toastify';

function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await axios.get('/api/v1/events');
        setEvents(res.data);
      } catch (err) {
        toast.error('Failed to load events');
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  const filteredEvents = events.filter(event =>
    event.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div>Loading events...</div>;

  return (
    <div className="events-container">
      <h1>Upcoming Events</h1>
      
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search events..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="events-grid">
        {filteredEvents.map(event => (
          <div key={event._id} className="event-card">
            <h3>{event.name}</h3>
            <p>{new Date(event.date).toLocaleDateString()}</p>
            <p>{event.location}</p>
            <Link to={`/events/${event._id}`} className="btn">
              View Details
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Events;
