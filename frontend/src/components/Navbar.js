import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav style={{ padding: '1rem', background: '#f0f0f0' }}>
      <Link to="/admin" style={{ marginRight: '1rem' }}>Admin</Link>
      <Link to="/checkin">Peserta</Link>
    </nav>
  );
}

export default Navbar;