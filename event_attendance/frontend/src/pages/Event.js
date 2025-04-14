import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../axiosInstance';
import { toast } from 'react-toastify';

function Event() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isRegistered, setIsRegistered] = useState(false);
  const [registrationLoading, setRegistrationLoading] = useState(false);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const res = await axios.get(`/api/v1/events/${id}`);
        setEvent(res.data);
        
        // Check if user is already registered
        const registrationRes = await axios.get('/api/v1/attendees/my-registrations');
        const isReg = registrationRes.data.some(reg => reg.event._id === id);
        setIsRegistered(isReg);
      } catch (err) {
        toast.error('Failed to load event details');
        navigate('/events');
      } finally {
        setLoading(false);
      }
    };
    fetchEvent();
  }, [id, navigate]);

  const handleRegister = async () => {
    setRegistrationLoading(true);
    try {
      await axios.post(`/api/v1/attendees/register/${id}`);
      toast.success('Successfully registered for this event!');
      setIsRegistered(true);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Registration failed');
    } finally {
      setRegistrationLoading(false);
    }
  };

  if (loading) return <div>Loading event details...</div>;

  return (
    <div className="event-detail-container">
      <h1>{event.name}</h1>
      <div className="event-meta">
        <p><strong>Date:</strong> {new Date(event.date).toLocaleString()}</p>
        <p><strong>Location:</strong> {event.location}</p>
        <p><strong>Description:</strong> {event.description}</p>
      </div>

      {isRegistered ? (
        <div className="registration-status">
          <p>You are registered for this event</p>
          <button 
            className="btn"
            onClick={() => navigate('/my-registrations')}
          >
            View My Registrations
          </button>
        </div>
      ) : (
        <button 
          className="btn btn-primary"
          onClick={handleRegister}
          disabled={registrationLoading}
        >
          {registrationLoading ? 'Registering...' : 'Register for Event'}
        </button>
      )}
    </div>
  );
}

export default Event;
