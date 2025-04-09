import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../components/admin/Login';
import EventList from '../components/admin/EventList';
import CreateEventForm from '../components/admin/CreateEventForm';
import AttendeeList from '../components/admin/AttendeeList';

const AdminPage = () => {
  const token = localStorage.getItem('token');

  if (!token) {
    return <Navigate to="/admin/login" />;
  }

  return (
    <div className="admin-page">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<EventList />} />
        <Route path="/create-event" element={<CreateEventForm />} />
        <Route path="/events/:eventId/attendees" element={<AttendeeList />} />
      </Routes>
    </div>
  );
};

export default AdminPage;