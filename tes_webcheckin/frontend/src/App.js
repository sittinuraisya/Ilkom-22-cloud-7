import logo from './logo.svg';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import AdminPage from './pages/Admin/AdminPage';
import CheckInPage from './pages/Peserta/CheckInPage';
import Navbar from './components/Navbar';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', 
    },
    secondary: {
      main: '#dc004e', 
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navbar />
        <Routes>
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/checkin" element={<CheckInPage />} />
          <Route path="/" element={<CheckInPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;