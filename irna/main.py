import os
import time
import sys
import platform
from datetime import datetime
from core.menu import show_main_menu

APP_NAME = "🍽️  FOOD RECOMMENDER 🍽️"
VERSION = "v1.0.0"
AUTHOR = "irnawati"
MIN_PYTHON = (3, 7)
LOG_FILE = "app.log"

# ====== Utilitas Tampilan ======
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print("=" * 60)
    print(APP_NAME.center(60))
    print("=" * 60)
    print(f"Versi : {VERSION}")
    print(f"Author: {AUTHOR}")
    print(f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print("-" * 60)

def loading_animation(text="Memuat aplikasi"):
    for i in range(4):
        dots = '.' * (i % 4)
        print(f"{text}{dots}".ljust(40), end='\r')
        time.sleep(0.4)
    print(" " * 40, end="\r")

def system_info():
    print("📦 Info Sistem")
    print(f"- Python Version : {sys.version.split()[0]}")
    print(f"- OS             : {platform.system()} {platform.release()}")
    print(f"- Platform       : {platform.platform()}")
    print("-" * 60)

def credits():
    print("\n✨ Makasih udah pake *Food Recommender*!")
    print("  Semoga kamu nemu makanan yang pas di hati. ❤️")
    print("  Balik lagi kalau lapar, ya! 🍽️ 🙌")
    print("=" * 60)

# ====== Validasi Versi ======
def check_python_version():
    if sys.version_info < MIN_PYTHON:
        print(f"❌ Python minimal versi {'.'.join(map(str, MIN_PYTHON))} diperlukan.")
        sys.exit(1)

# ====== Bantuan & Logging ======
def show_help():
    print("\n❓ Bantuan")
    print("  - Program ini membantu kamu mencari, menambah, mengedit resep.")
    print("  - Navigasi dengan memilih angka menu.")
    print("  - Tekan Ctrl+C kapan saja untuk keluar.")
    print("  - Versi saat ini: ", VERSION)
    print("  - Developer     : ", AUTHOR)
    print("-" * 60)

def log_aktivitas(pesan):
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{waktu}] {pesan}\n")

def fake_update_check():
    print("🔎 Mengecek update terbaru...")
    time.sleep(1)
    print("✅ Aplikasi sudah versi terbaru.\n")

def konfigurasi_pengguna():
    print("\n⚙️  Pengaturan Pengguna")
    nama = input("Masukkan nama kamu: ").strip()
    if nama:
        print(f"✅ Hai {nama}, pengaturan disimpan sementara~")
    else:
        print("❌ Nama tidak boleh kosong.")

# ====== Fungsi Dummy Tambahan ======
def dummy_pengujian_fitur():
    print("\n🧪 Pengujian fitur dimulai...")
    fitur = ["akses data", "pencarian", "simpan", "hapus", "edit", "load ulang", "backup", "restore"]
    for f in fitur:
        print(f"- Menguji {f}...")
        time.sleep(0.2)
    print("✅ Semua fitur dummy berhasil diuji.\n")

def log_dummy_interaksi():
    interaksi = [
        "User membuka aplikasi",
        "User melihat daftar resep",
        "User mencari resep 'Nasi Goreng'",
        "User menambahkan resep baru",
        "User mengedit data resep",
        "User membuka menu bantuan",
        "User keluar dari aplikasi"
    ]
    print("📋 Simulasi log aktivitas pengguna:")
    for aktivitas in interaksi:
        log_aktivitas(aktivitas)
        print(f"  > {aktivitas}")
        time.sleep(0.2)

def tampilkan_tentang():
    print("\nℹ️ Tentang Aplikasi")
    print("  Aplikasi ini dibuat untuk membantu kamu menemukan inspirasi makanan.")
    print("  Dengan fitur pencarian, tambah, dan edit resep makanan Indonesia.")
    print("  Dikembangkan oleh Irnawati ❤️")
    print("-" * 60)

def tips_acak():
    tips = [
        "📝 Tips: Gunakan bawang merah dan putih segar untuk rasa maksimal.",
        "🔥 Tips: Panaskan wajan terlebih dahulu sebelum memasak.",
        "🌶️ Tips: Tambahkan cabai rawit sesuai selera agar makin mantap!",
        "🍚 Tips: Nasi kemarin lebih cocok untuk nasi goreng.",
        "🧂 Tips: Jangan terlalu banyak garam, cicipi dulu ya!",
        "🍗 Tips: Marinasi ayam minimal 30 menit agar lebih meresap.",
        "🥦 Tips: Jangan rebus sayur terlalu lama, nutrisinya bisa hilang.",
        "🥕 Tips: Iris sayur searah serat agar tekstur tetap renyah."
    ]
    print("\n📌 Tips Memasak Hari Ini:")
    for t in tips:
        print(f"  - {t}")
        time.sleep(0.2)

def menu_utilitas():
    while True:
        print("\n🔧 Menu Utilitas")
        print("1. Lihat Tips Memasak")
        print("2. Simulasi Log Pengguna")
        print("3. Pengujian Fitur Dummy")
        print("4. Tentang Aplikasi")
        print("5. Bantuan")
        print("0. Kembali")
        pilih = input("Pilih menu: ")
        if pilih == "1":
            tips_acak()
        elif pilih == "2":
            log_dummy_interaksi()
        elif pilih == "3":
            dummy_pengujian_fitur()
        elif pilih == "4":
            tampilkan_tentang()
        elif pilih == "5":
            show_help()
        elif pilih == "0":
            break
        else:
            print("❌ Pilihan tidak tersedia.")

# ====== Fungsi Utama ======
def run_app():
    clear_screen()
    banner()
    check_python_version()
    loading_animation()
    system_info()
    fake_update_check()
    input("Tekan ENTER untuk melanjutkan ke menu utama...")
    clear_screen()
    banner()
    tips_acak()

    try:
        log_aktivitas("Aplikasi dijalankan")
        show_main_menu()
        menu_utilitas()
    finally:
        log_aktivitas("Aplikasi ditutup")
        credits()

# ====== Eksekusi ======
if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\n\n❗ Program dihentikan oleh pengguna.")
        log_aktivitas("Program dihentikan oleh pengguna.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {str(e)}")
        log_aktivitas(f"ERROR: {str(e)}")
        sys.exit(1)
