import { Card, TextField, Button, Typography } from '@mui/material';

function EventForm() {
  return (
    <Card sx={{ maxWidth: 600, margin: 'auto', p: 3 }}>
      <Typography variant="h5" gutterBottom>Buat Acara Baru</Typography>
      <TextField 
        label="Nama Acara" 
        fullWidth 
        margin="normal" 
      />
      <TextField 
        type="datetime-local" 
        fullWidth 
        margin="normal"
        InputLabelProps={{ shrink: true }}
      />
      <Button variant="contained" sx={{ mt: 2 }}>
        Simpan Acara
      </Button>
    </Card>
  );
}