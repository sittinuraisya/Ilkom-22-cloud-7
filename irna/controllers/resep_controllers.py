# controllers/resep_controller.py

import json
import os

DATA_FILE = "data/resep.json"
resep_list = []

# ======================= DATA HANDLING =========================
def load_resep():
    global resep_list
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                resep_list = json.load(f)
                print("📁 Resep berhasil dimuat.")
            except json.JSONDecodeError:
                resep_list = []
                print("⚠️ Data resep rusak, mulai dari kosong.")
    else:
        resep_list = []
        print("📁 Belum ada data resep, mulai dari kosong.")

def simpan_resep():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(resep_list, f, indent=4, ensure_ascii=False)
    print("💾 Resep berhasil disimpan.")

# ======================= CORE FUNCTION =========================
def lihat_resep():
    if not resep_list:
        print("📭 Belum ada resep.")
        return
    print("\n📖 Daftar Resep:")
    for i, resep in enumerate(resep_list, start=1):
        print(f"{i}. {resep['nama']} | Bahan: {', '.join(resep['bahan'])}")

def tambah_resep():
    nama = input("Nama resep: ").strip()
    if not nama:
        print("❌ Nama tidak boleh kosong.")
        return

    bahan = input("Masukkan bahan (pisahkan dengan koma): ").split(",")
    bahan = [b.strip() for b in bahan if b.strip()]
    
    if not bahan:
        print("❌ Bahan tidak valid.")
        return

    resep = {
        "nama": nama,
        "bahan": bahan
    }
    resep_list.append(resep)
    simpan_resep()
    print(f"✅ Resep '{nama}' berhasil ditambahkan!")

def hapus_resep():
    lihat_resep()
    if not resep_list:
        return
    try:
        idx = int(input("Masukkan nomor resep yang ingin dihapus: "))
        if 1 <= idx <= len(resep_list):
            resep = resep_list.pop(idx - 1)
            simpan_resep()
            print(f"🗑️ Resep '{resep['nama']}' berhasil dihapus.")
        else:
            print("❌ Nomor tidak valid.")
    except ValueError:
        print("❌ Input harus berupa angka.")

def edit_resep():
    lihat_resep()
    if not resep_list:
        return
    try:
        idx = int(input("Pilih nomor resep yang ingin diedit: "))
        if 1 <= idx <= len(resep_list):
            resep = resep_list[idx - 1]
            print(f"🔧 Edit Resep: {resep['nama']}")
            nama_baru = input("Nama baru (biarkan kosong jika tidak diubah): ").strip()
            bahan_baru = input("Bahan baru (pisahkan koma, kosongkan jika tidak diubah): ").strip()

            if nama_baru:
                resep["nama"] = nama_baru
            if bahan_baru:
                resep["bahan"] = [b.strip() for b in bahan_baru.split(",") if b.strip()]

            simpan_resep()
            print("✅ Resep berhasil diperbarui.")
        else:
            print("❌ Nomor tidak valid.")
    except ValueError:
        print("❌ Input harus berupa angka.")

def cari_resep():
    keyword = input("Masukkan kata kunci pencarian: ").lower()
    hasil = [r for r in resep_list if keyword in r['nama'].lower()]
    if not hasil:
        print("🔍 Tidak ditemukan resep yang sesuai.")
        return
    print("\n🎯 Hasil Pencarian:")
    for i, r in enumerate(hasil, start=1):
        print(f"{i}. {r['nama']} | Bahan: {', '.join(r['bahan'])}")

# ======================= MENU OPSI TAMBAHAN ====================
def menu_resep():
    load_resep()
    while True:
        print("\n📋 Menu Utama")
        print("1. Lihat Resep")
        print("2. Tambah Resep")
        print("3. Edit Resep")
        print("4. Cari Resep")
        print("5. Keluar")
        print("0. Kembali ke Menu Utama")

        pilihan = input("Pilih opsi: ")
        if pilihan == "1":
            lihat_resep()
        elif pilihan == "2":
            tambah_resep()
        elif pilihan == "3":
            hapus_resep()
        elif pilihan == "4":
            edit_resep()
        elif pilihan == "5":
            cari_resep()
        elif pilihan == "0":
            break
        else:
            print("❌ Pilihan tidak valid.")