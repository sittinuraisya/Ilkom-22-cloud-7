import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from '../axiosInstance';
import { toast } from 'react-toastify';

function MyRegistrations() {
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRegistrations = async () => {
      try {
        const res = await axios.get('/api/v1/attendees/my-registrations');
        setRegistrations(res.data);
      } catch (err) {
        toast.error('Failed to load your registrations');
      } finally {
        setLoading(false);
      }
    };
    fetchRegistrations();
  }, []);

  const handleCancel = async (registrationId) => {
    try {
      await axios.delete(`/api/v1/attendees/cancel/${registrationId}`);
      setRegistrations(registrations.filter(reg => reg._id !== registrationId));
      toast.success('Registration cancelled successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Cancellation failed');
    }
  };

  if (loading) return <div>Loading your registrations...</div>;

  return (
    <div className="registrations-container">
      <h1>My Event Registrations</h1>
      
      {registrations.length === 0 ? (
        <p>You haven't registered for any events yet.</p>
      ) : (
        <div className="registrations-list">
          {registrations.map(registration => (
            <div key={registration._id} className="registration-card">
              <h3>{registration.event.name}</h3>
              <p>Date: {new Date(registration.event.date).toLocaleString()}</p>
              <p>Location: {registration.event.location}</p>
              <p>Status: {registration.status}</p>
              
              <div className="registration-actions">
                <Link 
                  to={`/events/${registration.event._id}`}
                  className="btn"
                >
                  View Event
                </Link>
                
                {registration.status === 'registered' && (
                  <button
                    className="btn btn-danger"
                    onClick={() => handleCancel(registration._id)}
                  >
                    Cancel Registration
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default MyRegistrations;
