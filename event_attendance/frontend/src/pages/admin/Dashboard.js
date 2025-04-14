import { useState, useEffect } from 'react';
import axios from '../../axiosInstance';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';

function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalEvents: 0,
    totalUsers: 0,
    totalAttendees: 0,
    recentEvents: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('/api/v1/admin/stats');
        setStats(res.data);
      } catch (err) {
        toast.error('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div>Loading dashboard...</div>;

  return (
    <div className="admin-container">
      <h1>Admin Dashboard</h1>
      <p>Welcome back, {user?.name}</p>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Events</h3>
          <p>{stats.totalEvents}</p>
        </div>
        <div className="stat-card">
          <h3>Total Users</h3>
          <p>{stats.totalUsers}</p>
        </div>
        <div className="stat-card">
          <h3>Total Attendees</h3>
          <p>{stats.totalAttendees}</p>
        </div>
      </div>

      <div className="recent-events">
        <h2>Recent Events</h2>
        {stats.recentEvents.length > 0 ? (
          <ul>
            {stats.recentEvents.map(event => (
              <li key={event._id}>
                <h4>{event.name}</h4>
                <p>Date: {new Date(event.date).toLocaleDateString()}</p>
                <p>Attendees: {event.attendeeCount}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p>No recent events</p>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
