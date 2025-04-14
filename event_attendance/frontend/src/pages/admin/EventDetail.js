import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../../axiosInstance';
import { toast } from 'react-toastify';

function AdminEventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    date: '',
    location: '',
    maxAttendees: 0
  });
  const [attendees, setAttendees] = useState([]);
  const [attendeeLoading, setAttendeeLoading] = useState(true);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const res = await axios.get(`/api/v1/admin/events/${id}`);
        setEvent(res.data);
        setFormData({
          name: res.data.name,
          description: res.data.description,
          date: res.data.date.split('T')[0],
          location: res.data.location,
          maxAttendees: res.data.maxAttendees
        });
      } catch (err) {
        toast.error('Failed to load event details');
        navigate('/admin/events');
      } finally {
        setLoading(false);
      }
    };

    const fetchAttendees = async () => {
      try {
        const res = await axios.get(`/api/v1/admin/events/${id}/attendees`);
        setAttendees(res.data);
      } catch (err) {
        toast.error('Failed to load attendees');
      } finally {
        setAttendeeLoading(false);
      }
    };

    fetchEvent();
    fetchAttendees();
  }, [id, navigate]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.put(`/api/v1/admin/events/${id}`, formData);
      setEvent(res.data);
      setEditing(false);
      toast.success('Event updated successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update event');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    
    try {
      await axios.delete(`/api/v1/admin/events/${id}`);
      toast.success('Event deleted successfully');
      navigate('/admin/events');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete event');
    }
  };

  if (loading) return <div>Loading event details...</div>;

  return (
    <div className="admin-container">
      <div className="event-header">
        <h1>{event.name}</h1>
        <div className="event-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setEditing(!editing)}
          >
            {editing ? 'Cancel' : 'Edit Event'}
          </button>
          <button 
            className="btn btn-danger"
            onClick={handleDelete}
          >
            Delete Event
          </button>
        </div>
      </div>

      {editing ? (
        <form onSubmit={handleUpdate} className="event-form">
          <div className="form-group">
            <label>Event Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Date</label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({...formData, date: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Max Attendees</label>
            <input
              type="number"
              min="1"
              value={formData.maxAttendees}
              onChange={(e) => setFormData({...formData, maxAttendees: e.target.value})}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary">
            Save Changes
          </button>
        </form>
      ) : (
        <div className="event-details">
          <p><strong>Description:</strong> {event.description}</p>
          <p><strong>Date:</strong> {new Date(event.date).toLocaleString()}</p>
          <p><strong>Location:</strong> {event.location}</p>
          <p><strong>Max Attendees:</strong> {event.maxAttendees}</p>
          <p><strong>Current Attendees:</strong> {event.attendeeCount}</p>
        </div>
      )}

      <div className="attendees-section">
        <h2>Attendees</h2>
        {attendeeLoading ? (
          <p>Loading attendees...</p>
        ) : attendees.length > 0 ? (
          <table className="attendees-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Checked In</th>
              </tr>
            </thead>
            <tbody>
              {attendees.map(attendee => (
                <tr key={attendee._id}>
                  <td>{attendee.user.name}</td>
                  <td>{attendee.user.email}</td>
                  <td>{attendee.user.phone || '-'}</td>
                  <td>{attendee.checkedIn ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No attendees registered for this event yet.</p>
        )}
      </div>
    </div>
  );
}

export default AdminEventDetail;
