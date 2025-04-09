import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { QrReader } from 'react-qr-reader';
import axios from 'axios';
import { 
  Button, 
  TextField, 
  Paper, 
  Typography, 
  Box, 
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material';
import { CheckCircle, CameraAlt, Keyboard } from '@mui/icons-material';

function CheckInPage() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    nim: ''
  });
  const [scanEnabled, setScanEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handle QR Code Scan
  const handleScan = (data) => {
    if (data) {
      try {
        const scannedData = JSON.parse(data);
        setFormData({
          name: scannedData.name || '',
          email: scannedData.email || '',
          nim: scannedData.nim || ''
        });
        setScanEnabled(false);
        setAlert({
          open: true,
          message: 'Data berhasil di-scan!',
          severity: 'success'
        });
      } catch (error) {
        setAlert({
          open: true,
          message: 'Format QR Code tidak valid',
          severity: 'error'
        });
      }
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post('http://localhost:5000/api/checkin', {
        eventId,
        ...formData
      });
      
      setAlert({
        open: true,
        message: 'Check-in berhasil!',
        severity: 'success'
      });
      setTimeout(() => navigate('/'), 2000);
    } catch (error) {
      setAlert({
        open: true,
        message: error.response?.data?.message || 'Gagal melakukan check-in',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // Close alert
  const handleCloseAlert = () => {
    setAlert(prev => ({ ...prev, open: false }));
  };

  return (
    <Paper elevation={3} sx={{ 
      p: 4, 
      maxWidth: 600, 
      mx: 'auto', 
      my: 4,
      position: 'relative'
    }}>
      {/* Loading Overlay */}
      {loading && (
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255,255,255,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10
        }}>
          <CircularProgress size={60} />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Memproses data...
          </Typography>
        </Box>
      )}

      <Typography variant="h4" gutterBottom align="center">
        Check-In Acara
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant={scanEnabled ? 'contained' : 'outlined'}
          startIcon={<CameraAlt />}
          onClick={() => setScanEnabled(!scanEnabled)}
          disabled={loading}
        >
          {scanEnabled ? 'Tutup Scanner' : 'Scan QR Code'}
        </Button>
        <Button
          variant={!scanEnabled ? 'contained' : 'outlined'}
          startIcon={<Keyboard />}
          onClick={() => setScanEnabled(false)}
          disabled={loading}
        >
          Input Manual
        </Button>
      </Box>

      {scanEnabled ? (
        <Box sx={{ width: '100%', mb: 3 }}>
          <QrReader
            constraints={{ facingMode: 'environment' }}
            onResult={handleScan}
            style={{ width: '100%' }}
          />
          <Typography variant="caption" display="block" textAlign="center" sx={{ mt: 1 }}>
            Arahkan kamera ke QR Code
          </Typography>
        </Box>
      ) : (
        <form onSubmit={handleSubmit}>
          <TextField
            label="Nama Lengkap"
            name="name"
            fullWidth
            required
            margin="normal"
            value={formData.name}
            onChange={handleChange}
            disabled={loading}
          />
          <TextField
            label="Email"
            name="email"
            type="email"
            fullWidth
            margin="normal"
            value={formData.email}
            onChange={handleChange}
            disabled={loading}
          />
          <TextField
            label="NIM/Nomor Identitas"
            name="nim"
            fullWidth
            required
            margin="normal"
            value={formData.nim}
            onChange={handleChange}
            disabled={loading}
          />
          <Button
            type="submit"
            variant="contained"
            size="large"
            fullWidth
            sx={{ mt: 3 }}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={24} color="inherit" /> : null}
          >
            {loading ? 'Memproses...' : 'Submit Check-In'}
          </Button>
        </form>
      )}

      {/* Alert Notification */}
      <Snackbar
        open={alert.open}
        autoHideDuration={6000}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseAlert} 
          severity={alert.severity}
          sx={{ width: '100%' }}
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
}

export default CheckInPage;