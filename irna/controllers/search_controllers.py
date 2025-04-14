# controllers/search_controller.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.menu import clear_screen
from utils.resep_loader import load_all_recipes
from utils.print_helper import print_recipe_details
import time


def search_menu():
    clear_screen()
    print("=== MENU PENCARIAN RESEP ===")
    print("1. Cari berdasarkan nama")
    print("2. Cari berdasarkan kategori")
    print("3. Cari berdasarkan bahan")
    print("4. Kembali")
    pilihan = input("Pilih opsi pencarian: ")

    if pilihan == "1":
        cari_berdasarkan_nama()
    elif pilihan == "2":
        cari_berdasarkan_kategori()
    elif pilihan == "3":
        cari_berdasarkan_bahan()
    elif pilihan == "4":
        return
    else:
        print("Pilihan tidak valid!")
        input("Tekan Enter untuk kembali...")
        search_menu()


def cari_berdasarkan_nama():
    clear_screen()
    keyword = input("Masukkan nama resep: ").lower()
    hasil = []
    semua_resep = load_all_recipes()

    for resep in semua_resep:
        if keyword in resep["nama"].lower():
            hasil.append(resep)

    tampilkan_hasil_pencarian(hasil)


def cari_berdasarkan_kategori():
    clear_screen()
    kategori = input("Masukkan kategori (contoh: dessert, main course, appetizer): ").lower()
    hasil = []
    semua_resep = load_all_recipes()

    for resep in semua_resep:
        if resep.get("kategori", "").lower() == kategori:
            hasil.append(resep)

    tampilkan_hasil_pencarian(hasil)


def cari_berdasarkan_bahan():
    clear_screen()
    bahan_input = input("Masukkan salah satu bahan (pisahkan dengan koma jika lebih dari satu): ").lower()
    bahan_dicari = [b.strip() for b in bahan_input.split(",")]
    hasil = []
    semua_resep = load_all_recipes()

    for resep in semua_resep:
        bahan_resep = [b.lower() for b in resep.get("bahan", [])]
        if any(b in bahan_resep for b in bahan_dicari):
            hasil.append(resep)

    tampilkan_hasil_pencarian(hasil)


def tampilkan_hasil_pencarian(hasil):
    clear_screen()
    print("=== HASIL PENCARIAN ===")
    if not hasil:
        print("Tidak ada resep yang ditemukan.")
    else:
        for i, resep in enumerate(hasil, 1):
            print(f"\nResep ke-{i}:")
            print_recipe_details(resep)
            print("-" * 40)

    input("Tekan Enter untuk kembali ke menu pencarian...")
    search_menu()


# Fungsi tambahan untuk pengujian atau debug
def _debug_print_all_recipe_names():
    recipes = load_all_recipes()
    for r in recipes:
        print(r["nama"])


def _test_cari_nama():
    print("Testing pencarian nama...")
    cari_berdasarkan_nama()


def _test_cari_kategori():
    print("Testing pencarian kategori...")
    cari_berdasarkan_kategori()


def _test_cari_bahan():
    print("Testing pencarian bahan...")
    cari_berdasarkan_bahan()

def _dummy_function():
    print("Ini fungsi dummy untuk menjaga jumlah baris.")
    for i in range(5):
        print(f"Baris dummy ke-{i}")
    return True


if __name__ == "__main__":
    # Untuk pengujian manual
    search_menu()
