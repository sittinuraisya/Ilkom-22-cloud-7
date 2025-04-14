import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { user, logout, isImpersonating, stopImpersonating } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Event Attendance</Link>
        {isImpersonating && (
          <span className="impersonation-badge">Impersonating</span>
        )}
      </div>
      
      <div className="navbar-links">
        {user ? (
          <>
            <Link to="/events" className="nav-link">
              Events
            </Link>
            <Link to="/my-registrations" className="nav-link">
              My Registrations
            </Link>
            {isImpersonating ? (
              <button onClick={stopImpersonating} className="btn btn-warning">
                Stop Impersonation
              </button>
            ) : (
              <button onClick={logout} className="btn btn-danger">
                Logout
              </button>
            )}
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
    </nav>
  );
}

export default Navbar;
