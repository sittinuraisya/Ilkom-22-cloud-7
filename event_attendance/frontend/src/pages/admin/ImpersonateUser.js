import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../../axiosInstance';
import { toast } from 'react-toastify';

function ImpersonateUser() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get(`/api/v1/users/${userId}`);
        setUser(res.data);
      } catch (err) {
        toast.error('Failed to load user details');
        navigate('/admin/users');
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [userId, navigate]);

  const handleImpersonate = () => {
    localStorage.setItem('impersonatedUserId', userId);
    toast.success(`You are now impersonating ${user.name}`);
    navigate('/'); // Redirect to home or dashboard
  };

  if (loading) return <div>Loading user details...</div>;

  return (
    <div className="admin-container">
      <h1>Impersonate User</h1>
      {user ? (
        <div>
          <h2>{user.name}</h2>
          <p>Email: {user.email}</p>
          <p>Phone: {user.phone || '-'}</p>
          <button className="btn btn-primary" onClick={handleImpersonate}>
            Impersonate User
          </button>
        </div>
      ) : (
        <p>User not found</p>
      )}
    </div>
  );
}

export default ImpersonateUser;
