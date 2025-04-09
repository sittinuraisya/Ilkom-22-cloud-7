import { Paper, TextField, Button, Box } from '@mui/material';

function CheckInForm() {
  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 500, margin: 'auto' }}>
      <Box component="form">
        <TextField 
          label="Nama Lengkap" 
          fullWidth 
          margin="normal" 
          required
        />
        <Button 
          variant="contained" 
          fullWidth 
          sx={{ mt: 2 }}
        >
          Check-In
        </Button>
      </Box>
    </Paper>
  );
}