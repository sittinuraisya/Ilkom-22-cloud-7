# core/menu.py

resep_list = [
    {"nama": "Nasi Goreng", "bahan": ["minyak", "nasi", "bawang", "kecap", "telur", "seasoning"]},
    {"nama": "Mie Goreng", "bahan": ["mie instan", "minyak", "bawang", "kecap manis", "telur"]},
    {"nama": "Sate Ayam", "bahan": ["ayam", "bumbu kacang", "kecap", "bawang merah", "bawang putih"]},
    {"nama": "Nasi Uduk", "bahan": ["beras", "santan", "daun salam", "serai", "bawang goreng"]},
    {"nama": "Bubur Ayam", "bahan": ["beras", "ayam", "daun bawang", "bawang goreng", "kecap manis"]},
    {"nama": "Bakso", "bahan": ["daging sapi", "tepung sagu", "bawang putih", "garam", "merica"]},
    {"nama": "Rendang", "bahan": ["daging sapi", "santan", "bumbu rendang", "daun salam", "serai"]},
    {"nama": "Soto Ayam", "bahan": ["ayam", "bawang merah", "serai", "daun jeruk", "kunyit"]},
    {"nama": "Ayam Penyet", "bahan": ["ayam", "bawang putih", "cabai merah", "terasi", "kecap"]},
    {"nama": "Capcay", "bahan": ["kol", "wortel", "bawang putih", "daging ayam", "saos tiram"]},
    {"nama": "Sayur Asem", "bahan": ["kacang panjang", "labu", "melinjo", "daun salam", "asam"]},
    {"nama": "Gudeg", "bahan": ["nangka muda", "kelapa parut", "bumbu gudeg", "daun salam", "santan"]},
    {"nama": "Nasi Liwet", "bahan": ["beras", "santan", "daun salam", "serai", "ikan asin"]},
    {"nama": "Tahu Tempe Goreng", "bahan": ["tahu", "tempe", "bawang putih", "garam", "minyak goreng"]},
    {"nama": "Pecel", "bahan": ["kangkung", "taoge", "bumbu pecel", "tempe", "tahu"]},
    {"nama": "Pempek", "bahan": ["ikan tenggiri", "tepung sagu", "bawang putih", "air", "cuka"]},
    {"nama": "Lontong Sayur", "bahan": ["lontong", "santan", "kentang", "bumbu sayur", "daun salam"]},
    {"nama": "Ayam Goreng Kremes", "bahan": ["ayam", "bumbu ayam goreng", "tepung", "bawang putih", "minyak goreng"]},
    {"nama": "Ikan Bakar", "bahan": ["ikan", "bumbu bakar", "cabai", "bawang merah", "jeruk nipis"]},
    {"nama": "Karedok", "bahan": ["kol", "taoge", "timun", "bumbu kacang", "daun kemangi"]},
    {"nama": "Mie Rebus", "bahan": ["mie instan", "telur", "sawi", "kecap", "daun bawang"]},
    {"nama": "Bakmi Goreng", "bahan": ["mie telur", "ayam", "bawang", "kecap manis", "sayuran"]},
    {"nama": "Sambal Goreng Tahu Tempe", "bahan": ["tahu", "tempe", "cabai", "bawang merah", "kecap"]},
    {"nama": "Ayam Bakar Taliwang", "bahan": ["ayam", "cabai", "bawang merah", "terasi", "bumbu bakar"]},
    {"nama": "Mie Ayam", "bahan": ["mie", "ayam", "bawang putih", "saos tiram", "daun bawang"]},
    {"nama": "Kwetiau Siram", "bahan": ["kwetiau", "bawang putih", "daging sapi", "saos tiram", "sawi"]},
    {"nama": "Sop Buntut", "bahan": ["buntut sapi", "wortel", "kentang", "bawang putih", "daun bawang"]},
    {"nama": "Gulai Kambing", "bahan": ["daging kambing", "santan", "bumbu gulai", "daun salam", "serai"]},
    {"nama": "Martabak Telur", "bahan": ["telur", "daging cincang", "bawang", "daun bawang", "kecap manis"]},
    {"nama": "Cireng", "bahan": ["tepung aci", "air", "bawang putih", "garam", "minyak goreng"]},
    {"nama": "Klepon", "bahan": ["ketan", "air daun pandan", "gula merah", "kelapa parut", "garam"]},
    {"nama": "Nasi Kuning", "bahan": ["beras", "kunyit", "santan", "daun salam", "bawang goreng"]},
    {"nama": "Sambal Matah", "bahan": ["cabai", "bawang merah", "serai", "minyak kelapa", "garam"]},
    {"nama": "Gado-Gado", "bahan": ["kentang", "taoge", "sayuran", "bumbu kacang", "kerupuk"]},
    {"nama": "Tumis Kangkung", "bahan": ["kangkung", "bawang putih", "cabai", "saos tiram", "minyak"]},
    {"nama": "Tumis Tahu Tempe", "bahan": ["tahu", "tempe", "bawang putih", "cabai", "minyak goreng"]},
    {"nama": "Es Teh Manis", "bahan": ["teh", "gula", "air", "es batu"]},
    {"nama": "Es Buah", "bahan": ["melon", "semangka", "nanas", "sirup", "es batu"]},
    {"nama": "Es Krim", "bahan": ["krim", "gula", "susu", "perasa vanila"]},
    {"nama": "Pempek Lenjer", "bahan": ["ikan tenggiri", "tepung sagu", "bawang putih", "cuka", "air"]},
    {"nama": "Sop Ayam", "bahan": ["ayam", "kentang", "wortel", "bawang", "seledri"]},
    {"nama": "Telur Dadar", "bahan": ["telur", "bawang", "daun bawang", "garam", "merica"]},
    {"nama": "Pizza", "bahan": ["adonan pizza", "saus tomat", "keju", "tomat", "sosis"]},
    {"nama": "Pasta", "bahan": ["pasta", "saus tomat", "bawang putih", "daging ayam", "keju"]},
    {"nama": "Kue Cubir", "bahan": ["tepung terigu", "gula", "telur", "vanili", "baking powder"]},
    {"nama": "Curry Ayam", "bahan": ["ayam", "kari", "santan", "kentang", "bawang"]},
    {"nama": "Bubur Ketan Hitam", "bahan": ["ketan hitam", "santan", "gula merah", "garam"]},
    {"nama": "Lemper", "bahan": ["ketan", "ayamsuwir", "daun pisang", "kelapa parut"]},
    {"nama": "Roti Bakar", "bahan": ["roti tawar", "selai kacang", "mentega", "keju"]},
    {"nama": "Lontong", "bahan": ["beras", "daun pisang", "garam", "air"]},
    {"nama": "Dadar Gulung", "bahan": ["tepung terigu", "telur", "daun pandan", "kelapa parut"]},
    {"nama": "Kue Lapis", "bahan": ["tepung beras", "gula", "air daun pandan", "santan"]},
    {"nama": "Martabak Manis", "bahan": ["tepung terigu", "gula", "telur", "cokelat", "keju"]},
    {"nama": "Es Teler", "bahan": ["alpukat", "kelapa muda", "nangka", "sirup", "es batu"]},
    {"nama": "Mie Tiauw", "bahan": ["kwetiau", "bawang putih", "sawi", "daging ayam", "kecap manis"]},
    {"nama": "Lontong Cap Go Meh", "bahan": ["lontong", "sayur", "daging ayam", "bawang putih", "kecap manis"]},
    {"nama": "Bubur Sumsum", "bahan": ["tepung beras", "santan", "gula merah", "air daun pandan"]},
    {"nama": "Kerupuk Udang", "bahan": ["udang", "tepung tapioka", "bawang putih", "garam", "minyak"]},
    {"nama": "Cenil", "bahan": ["tepung ketan", "air daun pandan", "kelapa parut", "gula merah"]},
    {"nama": "Ayam Goreng Mentega", "bahan": ["ayam", "mentega", "bawang putih", "kecap manis", "garam"]},
    {"nama": "Pindang Ikan", "bahan": ["ikan", "air", "bumbu pindang", "daun salam", "cabai"]},
    {"nama": "Nasi Goreng Kampung", "bahan": ["nasi", "bawang putih", "cabe merah", "telur", "kecap manis"]},
    {"nama": "Sayur Lodeh", "bahan": ["tempe", "terong", "kelapa", "kacang panjang", "santan"]},
    {"nama": "Tahu Bacem", "bahan": ["tahu", "gula merah", "santannya", "bawang", "kecap manis"]},
    {"nama": "Curry Tempe", "bahan": ["tempe", "santan", "bumbu kari", "kentang", "daun kari"]},
    {"nama": "Nasi Bakar", "bahan": ["beras", "daun pisang", "santan", "bawang", "ikan teri"]},
    {"nama": "Roti Canai", "bahan": ["tepung terigu", "gula", "air", "minyak", "ghee"]},
    {"nama": "Tumis Daging Kacang Polong", "bahan": ["daging sapi", "kacang polong", "bawang putih", "saos tiram", "minyak"]},
    {"nama": "Bubur Sumsum", "bahan": ["tepung beras", "santan", "gula merah", "air daun pandan"]},
    {"nama": "Bakpao", "bahan": ["tepung terigu", "gula", "ragi", "daging ayam", "minyak"]},
    {"nama": "Ayam Kecap", "bahan": ["ayam", "kecap manis", "bawang putih", "daun bawang", "cabai"]},
    {"nama": "Gulai Sayur", "bahan": ["kacang panjang", "labu", "bumbu gulai", "santan", "cabai"]},
    {"nama": "Soto Madura", "bahan": ["daging sapi", "bawang putih", "daun jeruk", "serai", "kentang"]},
    {"nama": "Mie Goreng Jawa", "bahan": ["mie", "bawang merah", "saus tiram", "kecap manis", "cabai"]},
    {"nama": "Gado-Gado", "bahan": ["sayuran", "tempe", "tahu", "bumbu kacang", "kerupuk"]},
    {"nama": "Sup Bening Sayuran", "bahan": ["wortel", "kacang polong", "kentang", "bawang putih", "seledri"]},
    {"nama": "Pepes Ikan", "bahan": ["ikan", "daun pisang", "bumbu pepes", "cabai", "tomat"]},
    {"nama": "Tahu Tempe Bacem", "bahan": ["tahu", "tempe", "bawang putih", "kecap manis", "gula merah"]},
    {"nama": "Tumis Terong Pedas", "bahan": ["terong", "cabai", "bawang putih", "saos tiram", "minyak"]},
    {"nama": "Kwetiau Siram", "bahan": ["kwetiau", "sawi", "daging ayam", "saus tiram", "telur"]},
    {"nama": "Soto Ayam", "bahan": ["ayam", "bawang putih", "seledri", "daun jeruk", "santan"]},
    {"nama": "Pempek Palembang", "bahan": ["ikan tenggiri", "tepung sagu", "bawang putih", "telur", "air"]},
    {"nama": "Bakso", "bahan": ["daging sapi", "tepung tapioka", "bawang putih", "garam", "merica"]},
    {"nama": "Tumis Jamur", "bahan": ["jamur", "bawang putih", "saos tiram", "minyak", "garam"]},
    {"nama": "Ceker Ayam", "bahan": ["ceker ayam", "bawang putih", "cabai", "daun jeruk", "saos tiram"]},
]


def show_main_menu():
    while True:
        print("\n📋 Menu Utama")
        print("1. Lihat Resep")
        print("2. Tambah Resep")
        print("3. Edit Resep")
        print("4. Cari Resep")
        print("5. Keluar")
        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            tampilkan_resep()
        elif pilihan == "2":
            tambah_resep()
        elif pilihan == "3":
            edit_resep()
        elif pilihan == "4":
            cari_resep()
        elif pilihan == "5":
            print("Keluar dari aplikasi...")
            break
        else:
            print("❌ Pilihan tidak valid. Coba lagi.")

def tampilkan_resep():
    print("\n Daftar Resep:")
    print(f"Jumlah resep yang ada: {len(resep_list)}")  # Tambahkan ini untuk melihat jumlah resep
    if not resep_list:
        print("Belum ada resep.")
        return
    for i, resep in enumerate(resep_list, start=1):
        print(f"{i}. {resep['nama']} - Bahan: {', '.join(resep['bahan'])}")

def tambah_resep():
    nama = input("Masukkan nama resep: ")
    bahan = input("Masukkan daftar bahan (pisahkan dengan koma): ")
    bahan_list = [b.strip() for b in bahan.split(",")]
    resep_baru = {"nama": nama, "bahan": bahan_list}
    resep_list.append(resep_baru)
    print(f" Resep '{nama}' berhasil ditambahkan!")

def edit_resep():
    tampilkan_resep()
    try:
        idx = int(input("Masukkan nomor resep yang ingin diedit: ")) - 1
        if 0 <= idx < len(resep_list):
            nama_baru = input("Masukkan nama baru (biarkan kosong jika tidak ingin diubah): ")
            bahan_baru = input("Masukkan bahan baru (pisahkan dengan koma, kosongkan jika tidak ingin diubah): ")

            if nama_baru:
                resep_list[idx]["nama"] = nama_baru
            if bahan_baru:
                resep_list[idx]["bahan"] = [b.strip() for b in bahan_baru.split(",")]

            print(" Resep berhasil diperbarui!")
        else:
            print(" Nomor resep tidak valid.")
    except ValueError:
        print(" Input harus berupa angka.")

def cari_resep():
    keyword = input("Masukkan kata kunci pencarian: ").lower()
    hasil = [r for r in resep_list if keyword in r['nama'].lower()]
    if hasil:
        print("\n🔍 Hasil Pencarian:")
        for i, r in enumerate(hasil, start=1):
            print(f"{i}. {r['nama']} - Bahan: {', '.join(r['bahan'])}")
    else:
        print(" Tidak ada resep yang ditemukan.")
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
