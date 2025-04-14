import json
import uuid
from datetime import datetime

class Resep:
    def __init__(self, nama: str, bahan: list, kategori: str = "Umum", langkah: list = None, id_resep=None, dibuat=None):
        self.id_resep = id_resep or str(uuid.uuid4())
        self.nama = nama
        self.bahan = bahan
        self.kategori = kategori
        self.langkah = langkah or []
        self.dibuat = dibuat or datetime.now().isoformat()

    def tampilkan(self):
        print(f"ID       : {self.id_resep}")
        print(f"Nama     : {self.nama}")
        print(f"Kategori : {self.kategori}")
        print("Bahan:")
        for b in self.bahan:
            print(f" - {b}")
        if self.langkah:
            print("Langkah-langkah:")
            for i, l in enumerate(self.langkah, 1):
                print(f" {i}. {l}")
        print(f"Dibuat   : {self.dibuat}")

    def ubah_nama(self, nama_baru: str):
        if nama_baru:
            self.nama = nama_baru.strip()

    def ubah_bahan(self, bahan_baru: list):
        if bahan_baru:
            self.bahan = [b.strip() for b in bahan_baru if b.strip()]

    def ubah_kategori(self, kategori_baru: str):
        if kategori_baru:
            self.kategori = kategori_baru.strip()

    def ubah_langkah(self, langkah_baru: list):
        if langkah_baru:
            self.langkah = [l.strip() for l in langkah_baru if l.strip()]

    def cocok_dengan_kata_kunci(self, keyword: str) -> bool:
        keyword = keyword.lower()
        return (
            keyword in self.nama.lower()
            or keyword in self.kategori.lower()
            or any(keyword in b.lower() for b in self.bahan)
            or any(keyword in l.lower() for l in self.langkah)
        )

    def to_dict(self):
        return {
            "id_resep": self.id_resep,
            "nama": self.nama,
            "kategori": self.kategori,
            "bahan": self.bahan,
            "langkah": self.langkah,
            "dibuat": self.dibuat
        }

    @staticmethod
    def from_dict(data: dict):
        return Resep(
            id_resep=data.get("id_resep"),
            nama=data.get("nama", ""),
            kategori=data.get("kategori", "Umum"),
            bahan=data.get("bahan", []),
            langkah=data.get("langkah", []),
            dibuat=data.get("dibuat")
        )

# Fitur bantu tambahan buat testing & debugging
def simpan_resep_ke_file(resep_list: list, filename="data_resep.json"):
    with open(filename, "w", encoding="utf-8") as f:
        data = [resep.to_dict() for resep in resep_list]
        json.dump(data, f, ensure_ascii=False, indent=4)

def muat_resep_dari_file(filename="data_resep.json") -> list:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Resep.from_dict(d) for d in data]
    except FileNotFoundError:
        return []

def tampilkan_semua_resep(resep_list: list):
    if not resep_list:
        print("Belum ada resep tersimpan.")
        return
    for i, resep in enumerate(resep_list, 1):
        print(f"\n[{i}]")
        resep.tampilkan()

def cari_resep_berdasarkan_kata_kunci(resep_list: list, keyword: str):
    hasil = [r for r in resep_list if r.cocok_dengan_kata_kunci(keyword)]
    if not hasil:
        print(f"Tidak ditemukan resep dengan kata kunci '{keyword}'.")
    else:
        print(f"Ditemukan {len(hasil)} resep:")
        tampilkan_semua_resep(hasil)

# Contoh testing lokal
if __name__ == "__main__":
    resep1 = Resep(
        nama="Nasi Goreng",
        bahan=["Nasi", "Bawang Putih", "Kecap", "Telur", "Minyak"],
        kategori="Masakan Utama",
        langkah=["Panaskan minyak", "Tumis bawang", "Masukkan nasi", "Tambahkan kecap", "Masukkan telur"]
    )
    resep2 = Resep(
        nama="Jus Alpukat",
        bahan=["Alpukat", "Susu Kental Manis", "Es Batu"],
        kategori="Minuman"
    )
    resep3 = Resep(
            nama="Ayam Goreng",
            bahan=["Ayam", "Bawang Putih", "Ketumbar", "Garam", "Minyak"],
            kategori="Masakan Utama",
            langkah=["Lumuri ayam dengan bumbu", "Diamkan 30 menit", "Goreng hingga matang"]
    )
    resep4 = Resep(
            nama="Mie Goreng",
            bahan=["Mie", "Sayuran", "Telur", "Kecap", "Bawang Merah"],
            kategori="Masakan Utama",
            langkah=["Rebus mie", "Tumis sayur", "Masukkan mie dan telur", "Tambahkan kecap"]
    )
    resep5 = Resep(
            nama="Sate Ayam",
            bahan=["Daging ayam", "Tusuk sate", "Bumbu kacang", "Kecap", "Bawang Merah"],
            kategori="Makanan",
            langkah=["Potong ayam", "Tusuk sate", "Bakar sate", "Sajikan dengan bumbu kacang"]
    )
    resep6 = Resep(
            nama="Es Teh Manis",
            bahan=["Teh", "Gula", "Es Batu"],
            kategori="Minuman",
            langkah=["Seduh teh", "Tambahkan gula", "Tuang ke gelas berisi es batu"]
     )
    resep7 = Resep(
            nama="Bakwan Sayur",
            bahan=["Wortel", "Kol", "Tepung", "Air", "Bawang Putih"],
            kategori="Gorengan",
            langkah=["Campur semua bahan", "Goreng hingga keemasan"]
    )
    resep8 = Resep(
            nama="Soto Ayam",
            bahan=["Ayam", "Soun", "Bumbu soto", "Bawang Goreng", "Telur Rebus"],
            kategori="Sup",
            langkah=["Rebus ayam dengan bumbu", "Suwir ayam", "Sajikan dengan pelengkap"]
    )
    resep9 = Resep(
            nama="Pisang Goreng",
            bahan=["Pisang", "Tepung Terigu", "Gula", "Minyak"],
            kategori="Gorengan",
            langkah=["Potong pisang", "Balur dengan tepung", "Goreng sampai matang"]
    )
    resep10 = Resep(
            nama="Nasi Uduk",
            bahan=["Beras", "Santan", "Daun Salam", "Serai", "Garam"],
            kategori="Masakan Utama",
            langkah=["Cuci beras", "Masak dengan santan dan rempah", "Kukus hingga matang"]
    )
    resep11 = Resep(
            nama="Kopi Susu",
            bahan=["Kopi", "Susu Kental Manis", "Air Panas"],
            kategori="Minuman",
            langkah=["Seduh kopi", "Tambahkan susu", "Aduk rata"]
    )
    resep12 = Resep(
            nama="Capcay Kuah",
            bahan=["Sayuran campur", "Bawang Putih", "Air", "Garam", "Sosis"],
            kategori="Masakan Cina",
            langkah=["Tumis bawang", "Masukkan sayuran", "Tambahkan air dan bumbu"]
    )
    resep13 = Resep(
            nama="Telur Dadar",
            bahan=["Telur", "Bawang Merah", "Cabai", "Garam"],
            kategori="Menu Harian",
            langkah=["Kocok telur dengan bahan", "Goreng hingga matang"]
    )
    resep14 = Resep(
            nama="Tempe Goreng",
            bahan=["Tempe", "Bawang Putih", "Ketumbar", "Garam"],
            kategori="Gorengan",
            langkah=["Iris tempe", "Rendam bumbu", "Goreng"]
    )
    resep15 = Resep(
            nama="Opor Ayam",
            bahan=["Ayam", "Santan", "Bumbu Opor", "Daun Salam", "Serai"],
            kategori="Lebaran",
            langkah=["Tumis bumbu", "Masukkan ayam", "Tuang santan", "Masak sampai matang"]
    )
    resep16 = Resep(
            nama="Smoothie Mangga",
            bahan=["Mangga", "Yogurt", "Madu", "Es Batu"],
            kategori="Minuman",
            langkah=["Kupas mangga", "Blender semua bahan", "Sajikan dingin"]
    )

    resep_list = [resep1, resep2, resep3, resep4, resep5]
    simpan_resep_ke_file(resep_list)
    print("Data tersimpan.\n")
    muat = muat_resep_dari_file()
    tampilkan_semua_resep(muat)
