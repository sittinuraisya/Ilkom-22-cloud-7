// checkin-api.js
// Express backend API untuk sistem kehadiran berbasis QR / input manual dengan fitur admin

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');
const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

// Dummy DB
const users = [
  { id: 1, name: 'Superadmin', email: 'superadmin@mail.com', role: 'superadmin' },
  { id: 2, name: 'Admin1', email: 'admin1@mail.com', role: 'admin' },
  { id: 3, name: 'Atasan1', email: 'atasan@mail.com', role: 'atasan' },
];

let pengajuan = [
  { id: 'PG001', email: 'pegawai1@mail.com', status: 'pending' },
];

const logs = [];

// Auth middleware
function verifyToken(req, res, next) {
  const bearer = req.headers['authorization'];
  if (!bearer) return res.status(403).json({ message: 'No token' });
  const token = bearer.split(' ')[1];
  try {
    const decoded = jwt.verify(token, 'secret');
    req.user = decoded;
    next();
  } catch (err) {
    res.status(403).json({ message: 'Invalid token' });
  }
}

function isAdmin(req, res, next) {
  if (req.user.role !== 'admin' && req.user.role !== 'superadmin') {
    return res.status(403).json({ message: 'Only admin' });
  }
  next();
}

// Auth login
app.post('/api/login', (req, res) => {
  const { email } = req.body;
  const user = users.find(u => u.email === email);
  if (!user) return res.status(404).json({ message: 'User not found' });

  const token = jwt.sign(user, 'secret', { expiresIn: '2h' });
  res.json({ token });
});

// Get pengajuan pending (atasan)
app.get('/api/pengajuan/pending', verifyToken, (req, res) => {
  if (req.user.role !== 'atasan') return res.status(403).json({ message: 'Forbidden' });
  res.json(pengajuan.filter(p => p.status === 'pending'));
});

// Approve pengajuan (1-klik)
app.post('/api/pengajuan/approve', verifyToken, (req, res) => {
  if (req.user.role !== 'atasan') return res.status(403).json({ message: 'Forbidden' });
  const { id_pengajuan } = req.body;
  const pg = pengajuan.find(p => p.id === id_pengajuan);
  if (!pg || pg.status !== 'pending') return res.status(400).json({ message: 'Invalid or already processed' });

  pg.status = 'approved';
  logs.push({ user: req.user.email, aksi: 'APPROVE CUTI', waktu: new Date().toISOString() });
  res.json({ status: 'success', message: 'Pengajuan disetujui' });
});

// Delegasi tugas ke atasan lain
app.post('/api/pengajuan/delegasi', verifyToken, (req, res) => {
  const { to_email } = req.body;
  const target = users.find(u => u.email === to_email && u.role === 'atasan');
  if (!target) return res.status(400).json({ message: 'Delegasi gagal' });
  logs.push({ user: req.user.email, aksi: `DELEGASI KE ${to_email}`, waktu: new Date().toISOString() });
  res.json({ status: 'success', message: 'Tugas didelegasikan' });
});

// Admin: get user list
app.get('/api/user', verifyToken, isAdmin, (req, res) => {
  res.json(users);
});

// Admin: delete user
app.delete('/api/user/:id', verifyToken, isAdmin, (req, res) => {
  const id = parseInt(req.params.id);
  const target = users.find(u => u.id === id);
  if (!target) return res.status(404).json({ message: 'User not found' });
  if (target.role === 'superadmin') return res.status(403).json({ message: 'Cannot delete superadmin' });

  const idx = users.findIndex(u => u.id === id);
  users.splice(idx, 1);
  logs.push({ user: req.user.email, aksi: `DELETE USER ${target.email}`, waktu: new Date().toISOString() });
  res.json({ status: 'success', message: 'User deleted' });
});

// Audit log
app.get('/api/audit-log', verifyToken, isAdmin, (req, res) => {
  res.json(logs);
});

app.listen(PORT, () => {
  console.log(`API server running at http://localhost:${PORT}`);
});