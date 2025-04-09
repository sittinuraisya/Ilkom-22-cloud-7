// Fungsi untuk menghitung jumlah hari cuti (termasuk validasi)
document.addEventListener('DOMContentLoaded', function() {
    // Elemen form
    const tanggalMulai = document.querySelector('input[name="tanggal_mulai"]');
    const tanggalSelesai = document.querySelector('input[name="tanggal_selesai"]');
    const jumlahHari = document.querySelector('input[name="jumlah_hari"]');
    const formCuti = document.querySelector('#form-cuti');

    if (tanggalMulai && tanggalSelesai && jumlahHari) {
        // Set tanggal minimal (hari ini)
        const today = new Date().toISOString().split('T')[0];
        tanggalMulai.min = today;
        tanggalSelesai.min = today;

        // Event listeners
        tanggalMulai.addEventListener('change', function() {
            // Set tanggal selesai minimal sama dengan tanggal mulai
            tanggalSelesai.min = this.value;
            
            // Jika tanggal selesai < tanggal mulai, reset
            if (tanggalSelesai.value && tanggalSelesai.value < this.value) {
                tanggalSelesai.value = '';
                jumlahHari.value = '';
            }
            
            hitungHari();
            validasiWeekend(this);
        });

        tanggalSelesai.addEventListener('change', function() {
            hitungHari();
            validasiWeekend(this);
        });

        // Validasi sebelum submit
        if (formCuti) {
            formCuti.addEventListener('submit', function(e) {
                if (!validasiTanggalCuti()) {
                    e.preventDefault();
                }
            });
        }
    }

    // Fungsi hitung hari kerja (exclude weekend)
    function hitungHari() {
        if (tanggalMulai.value && tanggalSelesai.value) {
            const start = new Date(tanggalMulai.value);
            const end = new Date(tanggalSelesai.value);
            
            // Validasi tanggal selesai tidak sebelum tanggal mulai
            if (end < start) {
                alert('Tanggal selesai tidak boleh sebelum tanggal mulai');
                tanggalSelesai.value = '';
                jumlahHari.value = '';
                return;
            }

            let totalDays = 0;
            let currentDate = new Date(start);
            
            // Hitung hari kerja (Senin-Jumat)
            while (currentDate <= end) {
                const day = currentDate.getDay();
                if (day !== 0 && day !== 6) { // Bukan Minggu (0) atau Sabtu (6)
                    totalDays++;
                }
                currentDate.setDate(currentDate.getDate() + 1);
            }

            jumlahHari.value = totalDays > 0 ? totalDays : '';
        } else {
            jumlahHari.value = '';
        }
    }

    // Validasi weekend
    function validasiWeekend(input) {
        if (input.value) {
            const date = new Date(input.value);
            const day = date.getDay();
            
            if (day === 0 || day === 6) {
                alert('Tanggal tidak boleh jatuh pada hari Sabtu atau Minggu');
                input.value = '';
                jumlahHari.value = '';
                return false;
            }
        }
        return true;
    }

    // Validasi lengkap sebelum submit
    function validasiTanggalCuti() {
        if (!tanggalMulai.value || !tanggalSelesai.value) {
            alert('Tanggal mulai dan selesai harus diisi');
            return false;
        }

        const start = new Date(tanggalMulai.value);
        const end = new Date(tanggalSelesai.value);
        
        if (end < start) {
            alert('Tanggal selesai tidak boleh sebelum tanggal mulai');
            return false;
        }

        if (!jumlahHari.value || jumlahHari.value <= 0) {
            alert('Tidak ada hari kerja dalam rentang tanggal tersebut');
            return false;
        }

        return true;
    }

    // Toast notification
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        return toast;
    });
});

// static/js/user.js
document.addEventListener('DOMContentLoaded', function() {
    // Pastikan semua link cetak memiliki target blank
    document.querySelectorAll('.btn-cetak').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.hasAttribute('target')) {
                this.setAttribute('target', '_blank');
            }
        });
    });
});

// static/js/loading.js
document.addEventListener('DOMContentLoaded', function() {
    // Tangkap semua form dengan class loading-form
    const forms = document.querySelectorAll('.loading-form');
    
    forms.forEach(form => {
      form.addEventListener('submit', function() {
        // Tampilkan loading overlay
        document.getElementById('loading-overlay').style.display = 'flex';
        
        // Optional: Disable tombol submit
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(button => {
          button.disabled = true;
          button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Memproses...';
        });
      });
    });
    
    // Sembunyikan loading ketika halaman selesai dimuat
    window.addEventListener('load', function() {
      document.getElementById('loading-overlay').style.display = 'none';
    });
  });


  