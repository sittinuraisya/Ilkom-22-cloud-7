import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

DATA_FILE = "keuangan.json"
KATEGORI = ["Makan", "Transport", "Gaji", "Belanja", "Hiburan", "Lainnya"]

class KeuanganApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💰 Aplikasi Keuangan Pribadi")
        self.transaksi = []
        self.filtered_data = []

        self.load_data()
        self.setup_ui()
        self.refresh_table()
        self.update_summary()

    def setup_ui(self):
        frame_input = tk.LabelFrame(self.root, text="Form Transaksi", padx=10, pady=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_input, text="Tanggal (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        self.tanggal_entry = tk.Entry(frame_input)
        self.tanggal_entry.grid(row=0, column=1, padx=5)
        self.tanggal_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(frame_input, text="Deskripsi:").grid(row=1, column=0, sticky="w")
        self.desc_entry = tk.Entry(frame_input)
        self.desc_entry.grid(row=1, column=1, padx=5)

        tk.Label(frame_input, text="Kategori:").grid(row=2, column=0, sticky="w")
        self.kat_cb = ttk.Combobox(frame_input, values=KATEGORI)
        self.kat_cb.grid(row=2, column=1, padx=5)

        tk.Label(frame_input, text="Jumlah (+/-):").grid(row=3, column=0, sticky="w")
        self.jumlah_entry = tk.Entry(frame_input)
        self.jumlah_entry.grid(row=3, column=1, padx=5)

        self.btn_simpan = tk.Button(frame_input, text="💾 Simpan", command=self.simpan_transaksi)
        self.btn_simpan.grid(row=4, column=0, columnspan=2, pady=10)

        # Filter dan Pencarian
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Filter Kategori:").pack(side="left")
        self.filter_kat_cb = ttk.Combobox(filter_frame, values=["Semua"] + KATEGORI, width=15)
        self.filter_kat_cb.current(0)
        self.filter_kat_cb.pack(side="left", padx=5)
        self.filter_kat_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        tk.Label(filter_frame, text="Tanggal (opsional):").pack(side="left")
        self.filter_date_entry = tk.Entry(filter_frame, width=12)
        self.filter_date_entry.pack(side="left", padx=5)
        self.filter_date_entry.insert(0, "")

        self.btn_filter = tk.Button(filter_frame, text="🔍 Filter", command=self.refresh_table)
        self.btn_filter.pack(side="left", padx=5)

        self.btn_reset = tk.Button(filter_frame, text="🔄 Reset", command=self.reset_filter)
        self.btn_reset.pack(side="left", padx=5)

        # Tabel Transaksi
        table_frame = tk.Frame(self.root)
        table_frame.pack(padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=("Tanggal", "Deskripsi", "Kategori", "Jumlah"), show="headings")
        self.tree.heading("Tanggal", text="Tanggal")
        self.tree.heading("Deskripsi", text="Deskripsi")
        self.tree.heading("Kategori", text="Kategori")
        self.tree.heading("Jumlah", text="Jumlah (Rp)")

        self.tree.column("Tanggal", width=100)
        self.tree.column("Deskripsi", width=150)
        self.tree.column("Kategori", width=100)
        self.tree.column("Jumlah", width=100, anchor="e")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_item)

        # Tombol Edit dan Hapus
        aksi_frame = tk.Frame(self.root)
        aksi_frame.pack(padx=10, pady=5)

        self.btn_edit = tk.Button(aksi_frame, text="✏️ Edit", command=self.edit_transaksi)
        self.btn_edit.pack(side="left", padx=5)

        self.btn_delete = tk.Button(aksi_frame, text="🗑️ Hapus", command=self.hapus_transaksi)
        self.btn_delete.pack(side="left", padx=5)

        # Ringkasan
        summary_frame = tk.Frame(self.root)
        summary_frame.pack(padx=10, pady=10)

        self.label_total_masuk = tk.Label(summary_frame, text="Total Pemasukan: Rp 0")
        self.label_total_masuk.pack(anchor="w")

        self.label_total_keluar = tk.Label(summary_frame, text="Total Pengeluaran: Rp 0")
        self.label_total_keluar.pack(anchor="w")

        self.label_saldo = tk.Label(summary_frame, text="Saldo Akhir: Rp 0", font=("Arial", 12, "bold"))
        self.label_saldo.pack(anchor="w", pady=(5, 0))

    def simpan_transaksi(self):
        tanggal = self.tanggal_entry.get().strip()
        deskripsi = self.desc_entry.get().strip()
        kategori = self.kat_cb.get().strip()
        jumlah = self.jumlah_entry.get().strip()

        if not (tanggal and deskripsi and kategori and jumlah):
            messagebox.showwarning("Peringatan", "Semua field harus diisi.")
            return

        try:
            datetime.strptime(tanggal, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Peringatan", "Format tanggal salah.")
            return

        try:
            jumlah = float(jumlah)
        except ValueError:
            messagebox.showwarning("Peringatan", "Jumlah harus angka.")
            return

        transaksi = {
            "tanggal": tanggal,
            "deskripsi": deskripsi,
            "kategori": kategori,
            "jumlah": jumlah
        }

        if self.selected_item is not None:
            idx = self.tree.index(self.selected_item)
            self.transaksi[idx] = transaksi
            self.selected_item = None
        else:
            self.transaksi.append(transaksi)

        self.save_data()
        self.clear_form()
        self.refresh_table()
        self.update_summary()

    def select_item(self, event):
        item = self.tree.focus()
        if item:
            values = self.tree.item(item)["values"]
            self.tanggal_entry.delete(0, tk.END)
            self.tanggal_entry.insert(0, values[0])
            self.desc_entry.delete(0, tk.END)
            self.desc_entry.insert(0, values[1])
            self.kat_cb.set(values[2])
            self.jumlah_entry.delete(0, tk.END)
            self.jumlah_entry.insert(0, values[3])
            self.selected_item = item

    def clear_form(self):
        self.tanggal_entry.delete(0, tk.END)
        self.tanggal_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.desc_entry.delete(0, tk.END)
        self.kat_cb.set("")
        self.jumlah_entry.delete(0, tk.END)

    def reset_filter(self):
        self.filter_kat_cb.set("Semua")
        self.filter_date_entry.delete(0, tk.END)
        self.refresh_table()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.transaksi = json.load(f)
        else:
            self.transaksi = []

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.transaksi, f, indent=2)

    def edit_transaksi(self):
        if self.selected_item is None:
            messagebox.showinfo("Info", "Pilih transaksi terlebih dahulu.")
            return
        self.simpan_transaksi()

    def hapus_transaksi(self):
        if self.selected_item is None:
            messagebox.showinfo("Info", "Pilih transaksi yang ingin dihapus.")
            return
        idx = self.tree.index(self.selected_item)
        self.transaksi.pop(idx)
        self.selected_item = None
        self.save_data()
        self.refresh_table()
        self.update_summary()
