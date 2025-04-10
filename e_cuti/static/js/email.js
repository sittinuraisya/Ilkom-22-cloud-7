// Handler pengiriman email
function sendNotificationEmail(userEmail, type) {
    fetch('/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail, type: type })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Email terkirim');
        }
    });
}