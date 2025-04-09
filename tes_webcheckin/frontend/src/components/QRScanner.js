import { QrReader } from 'react-qr-reader';
import { Dialog, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

function QRScanner({ open, onClose, onScan }) {
  return (
    <Dialog open={open} onClose={onClose}>
      <IconButton onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8 }}>
        <CloseIcon />
      </IconButton>
      <QrReader
        onResult={(result) => {
          if (result) onScan(result?.text);
        }}
        constraints={{ facingMode: 'environment' }}
      />
    </Dialog>
  );
}