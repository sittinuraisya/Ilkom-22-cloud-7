import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const AttendeeList = () => {
  const { eventId } = useParams();
  const [attendees, setAttendees] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAttendees = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${process.env.REACT_APP_API_URL}/attendance/${eventId}`, {
          headers: { 'x-auth-token': token },
        });
        setAttendees(res.data);
        setLoading(false);
      } catch (err) {
        console.error(err.response.data);
        setLoading(false);
      }
    };

    fetchAttendees();
  }, [eventId]);

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${process.env.REACT_APP_API_URL}/attendance/export/${eventId}`, {
        headers: { 'x-auth-token': token },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'attendees.xlsx');
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="attendee-list">
      <h2>Attendees</h2>
      <button onClick={handleExport}>Export to Excel</button>
      {attendees.length === 0 ? (
        <p>No attendees yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>NIM</th>
              <th>Check-In Time</th>
              <th>Method</th>
            </tr>
          </thead>
          <tbody>
            {attendees.map(attendee => (
              <tr key={attendee._id}>
                <td>{attendee.name}</td>
                <td>{attendee.email || '-'}</td>
                <td>{attendee.nim || '-'}</td>
                <td>{new Date(attendee.checkInTime).toLocaleString()}</td>
                <td>{attendee.checkInMethod}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default AttendeeList;