// Handler sinkronisasi kalender
document.querySelectorAll('.sync-calendar').forEach(button => {
    button.addEventListener('click', async () => {
        const cutiId = button.dataset.cutiId;
        try {
            const response = await fetch(`/sync-calendar/${cutiId}`);
            const result = await response.json();
            
            if (response.ok) {
                alert('Event berhasil disinkronisasi ke Google Calendar');
                button.innerHTML = '<i class="fas fa-check"></i> Synced';
                button.classList.remove('btn-info');
                button.classList.add('btn-success');
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert(`Gagal sync: ${error.message}`);
        }
    });
});