import os
import json

FILE_NAME = "reseps.txt"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_reseps():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_reseps(reseps):
    with open(FILE_NAME, 'w') as f:
        json.dump(reseps, f, indent=2)

def tampilkan_reseps(reseps):
    if not reseps:
        print("📭 Belum ada resep.\n")
        return
    print("📖 Daftar Resep:")
    for i, r in enumerate(reseps):
        print(f"{i+1}. {r['nama']}")
    print()

def tambah_resep(reseps):
    nama = input("🍲 Nama resep: ").strip()
    if not nama:
        print("❌ Nama tidak boleh kosong.")
        return

    print("\n📝 Masukkan bahan (ketik 'selesai' untuk mengakhiri):")
    bahan = []
    while True:
        b = input("- ")
        if b.lower() == 'selesai':
            break
        if b:
            bahan.append(b)

    print("\n👨‍🍳 Masukkan langkah memasak (ketik 'selesai'):")
    langkah = []
    while True:
        l = input("- ")
        if l.lower() == 'selesai':
            break
        if l:
            langkah.append(l)

    resep_baru = {
        'nama': nama,
        'bahan': bahan,
        'langkah': langkah
    }
    reseps.append(resep_baru)
    save_reseps(reseps)
    print("✅ Resep berhasil ditambahkan!\n")

def lihat_detail(reseps):
    tampilkan_reseps(reseps)
    if not reseps:
        return
    try:
        idx = int(input("Pilih nomor resep: ")) - 1
        if 0 <= idx < len(reseps):
            resep = reseps[idx]
            print(f"\n📌 Nama Resep: {resep['nama']}\n")

            print("🍽️ Bahan-bahan:")
            for b in resep['bahan']:
                print(f"- {b}")
            print("\n🔥 Langkah Memasak:")
            for i, l in enumerate(resep['langkah']):
                print(f"{i+1}. {l}")
            print()
        else:
            print("❌ Nomor tidak ditemukan.")
    except:
        print("❌ Input tidak valid.")

def hapus_resep(reseps):
    tampilkan_reseps(reseps)
    if not reseps:
        return
    try:
        idx = int(input("Nomor resep yang akan dihapus: ")) - 1
        if 0 <= idx < len(reseps):
            nama = reseps[idx]['nama']
            del reseps[idx]
            save_reseps(reseps)
            print(f"🗑️ Resep '{nama}' telah dihapus.")
        else:
            print("❌ Nomor tidak valid.")
    except:
        print("❌ Input tidak valid.")

def menu():
    print("== APLIKASI MEMASAK ==")
    print("1. Lihat semua resep")
    print("2. Lihat detail resep")
    print("3. Tambah resep")
    print("4. Hapus resep")
    print("5. Keluar")
    print("======================")

def main():
    reseps = load_reseps()
    while True:
        clear()
        menu()
        pilihan = input("Pilih menu (1-5): ").strip()
        if pilihan == '1':
            clear()
            tampilkan_reseps(reseps)
            input("Tekan Enter untuk kembali...")
        elif pilihan == '2':
            clear()
            lihat_detail(reseps)
            input("Tekan Enter untuk kembali...")
        elif pilihan == '3':
            clear()
            tambah_resep(reseps)
            input("Tekan Enter untuk kembali...")
        elif pilihan == '4':
            clear()
            hapus_resep(reseps)
            input("Tekan Enter untuk kembali...")
        elif pilihan == '5':
            print("👋 Sampai jumpa di dapur berikutnya!")
            break
        else:
            print("❌ Pilihan tidak valid.")
            input("Tekan Enter untuk kembali...")

if __name__ == '__main__':
    main()
