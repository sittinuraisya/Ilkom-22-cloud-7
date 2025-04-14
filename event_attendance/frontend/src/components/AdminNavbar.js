import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function AdminNavbar() {
  const { logout } = useAuth();

  return (
    <nav className="admin-navbar">
      <div className="admin-navbar-brand">
        <Link to="/admin">Admin Panel</Link>
      </div>
      
      <div className="admin-navbar-links">
        <Link to="/admin/dashboard" className="admin-nav-link">
          Dashboard
        </Link>
        <Link to="/admin/events" className="admin-nav-link">
          Events
        </Link>
        <Link to="/admin/users" className="admin-nav-link">
          Users
        </Link>
        <button onClick={logout} className="btn btn-danger">
          Logout
        </button>
      </div>
    </nav>
  );
}

export default AdminNavbar;
