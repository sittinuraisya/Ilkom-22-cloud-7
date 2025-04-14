import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">
          Event Attendance
        </Link>
        
        <div className="navbar-links">
          {isAuthenticated ? (
            <>
              <Link to="/events" className="nav-link">
                Events
              </Link>
              <Link to="/my-registrations" className="nav-link">
                My Registrations
              </Link>
              <button onClick={logout} className="btn btn-danger">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">
                Login
              </Link>
              <Link to="/register" className="nav-link">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
