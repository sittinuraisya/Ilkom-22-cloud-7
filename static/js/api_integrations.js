// Fungsi untuk mengirim reminder email
async function sendReminderEmail(email) {
    showLoading();
    try {
        const response = await fetch('/api/email/reminder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ email: email })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Gagal mengirim reminder');
        }
        
        showToast('Reminder berhasil dikirim', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Fungsi untuk export ke Excel
async function exportToExcel() {
    showLoading();
    try {
        const response = await fetch('/api/export/excel');
        
        if (!response.ok) {
            throw new Error('Gagal membuat file Excel');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'data_cuti.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Fungsi utilitas
function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type}`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}