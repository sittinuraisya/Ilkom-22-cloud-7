import QRCode from "qrcode.react";

function QRGenerator({ eventId }) {
  return (
    <div>
      <QRCode value={`https://yourapp.com/checkin/${eventId}`} />
    </div>
  );
}
