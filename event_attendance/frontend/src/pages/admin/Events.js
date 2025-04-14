import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from '../../axiosInstance';
import { toast } from 'react-toastify';

function AdminEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEvent, setNewEvent] = useState({
    name: '',
    description: '',
    date: '',
    location: '',
    maxAttendees: 100
  });

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await axios.get('/api/v1/admin/events');
        setEvents(res.data);
      } catch (err) {
        toast.error('Failed to load events');
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('/api/v1/admin/events', newEvent);
      setEvents([...events, res.data]);
      setShowCreateForm(false);
      setNewEvent({
        name: '',
        description: '',
        date: '',
        location: '',
        maxAttendees: 100
      });
      toast.success('Event created successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create event');
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    
    try {
      await axios.delete(`/api/v1/admin/events/${eventId}`);
      setEvents(events.filter(event => event._id !== eventId));
      toast.success('Event deleted successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete event');
    }
  };

  if (loading) return <div>Loading events...</div>;

  return (
    <div className="admin-container">
      <h1>Manage Events</h1>
      
      <button 
        className="btn btn-primary"
        onClick={() => setShowCreateForm(!showCreateForm)}
      >
        {showCreateForm ? 'Cancel' : 'Create New Event'}
      </button>

      {showCreateForm && (
        <form onSubmit={handleCreate} className="event-form">
          <div className="form-group">
            <label>Event Name</label>
            <input
              type="text"
              value={newEvent.name}
              onChange={(e) => setNewEvent({...newEvent, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={newEvent.description}
              onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Date & Time</label>
            <input
              type="datetime-local"
              value={newEvent.date}
              onChange={(e) => setNewEvent({...newEvent, date: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              value={newEvent.location}
              onChange={(e) => setNewEvent({...newEvent, location: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Max Attendees</label>
            <input
              type="number"
              min="1"
              value={newEvent.maxAttendees}
              onChange={(e) => setNewEvent({...newEvent, maxAttendees: e.target.value})}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary">
            Create Event
          </button>
        </form>
      )}

      <div className="events-list">
        {events.length > 0 ? (
          <table className="events-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Date</th>
                <th>Location</th>
                <th>Attendees</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {events.map(event => (
                <tr key={event._id}>
                  <td>
                    <Link to={`/admin/events/${event._id}`}>{event.name}</Link>
                  </td>
                  <td>{new Date(event.date).toLocaleString()}</td>
                  <td>{event.location}</td>
                  <td>{event.attendeeCount}/{event.maxAttendees}</td>
                  <td>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(event._id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No events found</p>
        )}
      </div>
    </div>
  );
}

export default AdminEvents;
