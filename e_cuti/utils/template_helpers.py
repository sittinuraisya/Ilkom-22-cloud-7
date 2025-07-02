def get_status_class(status):
    """Mengembalikan class CSS berdasarkan status cuti"""
    status_classes = {
        'Pending': 'bg-warning text-dark',
        'Disetujui': 'bg-success text-white',
        'Ditolak': 'bg-danger text-white',
        'Dibatalkan': 'bg-secondary text-white',
        'Dalam Review': 'bg-info text-dark'
    }
    return status_classes.get(status, 'bg-secondary text-white')

def get_jenis_class(jenis):
    """Mengembalikan class CSS berdasarkan jenis cuti"""
    jenis_classes = {
        'Cuti Tahunan': 'bg-primary text-white',
        'Cuti Sakit': 'bg-info text-dark',
        'Cuti Melahirkan': 'bg-pink text-white',
        'Cuti Besar': 'bg-purple text-white',
        'Cuti Karena Alasan Penting': 'bg-warning text-dark',
        'Cuti Tanpa Gaji': 'bg-secondary text-white',
        'Cuti Istimewa': 'bg-danger text-white'
    }
    return jenis_classes.get(jenis, 'bg-secondary text-white')