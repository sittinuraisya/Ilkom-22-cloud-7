import os
import datetime

# Barang disimpan sebagai list of dict
keranjang = []

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    print("="*40)
    print("     APLIKASI KASIR MINI - TERMINAL")
    print("="*40)

def tambah_barang():
    clear()
    header()
    nama = input("Nama barang      : ")
    try:
        harga = float(input("Harga satuan     : "))
        jumlah = int(input("Jumlah           : "))
        total = harga * jumlah
        barang = {
            'nama': nama,
            'harga': harga,
            'jumlah': jumlah,
            'total': total
        }
        keranjang.append(barang)
        print("✅ Barang ditambahkan ke keranjang.")
    except:
        print("❌ Input tidak valid.")
    input("\nTekan Enter untuk kembali...")

def tampilkan_keranjang():
    clear()
    header()
    if not keranjang:
        print("🛒 Keranjang kosong.\n")
    else:
        print("🛒 Daftar Barang:\n")
        print(f"{'No':<3} {'Nama':<15} {'Harga':>8} {'Qty':>5} {'Total':>10}")
        print("-"*45)
        for i, b in enumerate(keranjang):
            print(f"{i+1:<3} {b['nama']:<15} {b['harga']:>8.0f} {b['jumlah']:>5} {b['total']:>10.0f}")
        print("-"*45)
        total = sum(b['total'] for b in keranjang)
        print(f"{'':<25} Total: Rp {total:,.0f}")
    input("\nTekan Enter untuk kembali...")

def hapus_barang():
    clear()
    tampilkan_keranjang()
    if not keranjang:
        return
    try:
        no = int(input("Masukkan nomor barang yang dihapus: "))
        if 1 <= no <= len(keranjang):
            item = keranjang.pop(no-1)
            print(f"🗑️ Barang '{item['nama']}' dihapus.")
        else:
            print("❌ Nomor tidak valid.")
    except:
        print("❌ Input tidak valid.")
    input("\nTekan Enter untuk kembali...")

def checkout():
    clear()
    header()
    if not keranjang:
        print("Keranjang kosong.")
        input("\nTekan Enter untuk kembali...")
        return

    total = sum(b['total'] for b in keranjang)
    print(f"Total belanja : Rp {total:,.0f}")
    try:
        bayar = float(input("Bayar          : Rp "))
        if bayar < total:
            print("❌ Uang tidak cukup!")
            input("\nTekan Enter untuk kembali...")
            return
        kembalian = bayar - total
        cetak_struk(total, bayar, kembalian)
        print(f"✅ Transaksi selesai. Kembalian: Rp {kembalian:,.0f}")
        keranjang.clear()
    except:
        print("❌ Input tidak valid.")
    input("\nTekan Enter untuk kembali...")

def cetak_struk(total, bayar, kembalian):
    now = datetime.datetime.now()
    nama_file = f"struk_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(nama_file, 'w') as f:
        f.write("="*30 + "\n")
        f.write("        STRUK BELANJA\n")
        f.write("="*30 + "\n")
        for b in keranjang:
            f.write(f"{b['nama']} x{b['jumlah']} - Rp {b['total']:,.0f}\n")
        f.write("-"*30 + "\n")
        f.write(f"Total     : Rp {total:,.0f}\n")
        f.write(f"Bayar     : Rp {bayar:,.0f}\n")
        f.write(f"Kembalian : Rp {kembalian:,.0f}\n")
        f.write("="*30 + "\n")
        f.write("Terima kasih telah berbelanja!\n")
        f.write(now.strftime("Waktu: %d-%m-%Y %H:%M:%S\n"))
        f.write("="*30 + "\n")
    print(f"🧾 Struk disimpan sebagai '{nama_file}'")

def menu():
    while True:
        clear()
        header()
        print("1. Tambah Barang")
        print("2. Tampilkan Keranjang")
        print("3. Hapus Barang")
        print("4. Checkout")
        print("5. Keluar")
        print("="*40)
        pilih = input("Pilih menu [1-5]: ")
        if pilih == '1':
            tambah_barang()
        elif pilih == '2':
            tampilkan_keranjang()
        elif pilih == '3':
            hapus_barang()
        elif pilih == '4':
            checkout()
        elif pilih == '5':
            print("👋 Terima kasih, sampai jumpa!")
            break
        else:
            print("❌ Pilihan tidak valid.")
            input("\nTekan Enter untuk kembali...")

if __name__ == "__main__":
    menu()
