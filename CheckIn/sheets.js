const { google } = require('googleapis');
const path = require('path');

// Autentikasi via Service Account
const auth = new google.auth.GoogleAuth({
  keyFile: path.join(__dirname, 'credentials.json'), // Ganti dengan file credential JSON kamu
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

async function appendToSheet(data) {
  const client = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: client });

  const spreadsheetId = 'YOUR_SPREADSHEET_ID'; // Ganti dengan ID spreadsheet-mu
  const range = 'Sheet1!A1'; // atau posisi terakhir

  await sheets.spreadsheets.values.append({
    spreadsheetId,
    range,
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [data],
    },
  });

  console.log('✅ Data berhasil dikirim ke Google Sheets');
}

module.exports = { appendToSheet };