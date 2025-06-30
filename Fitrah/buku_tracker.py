import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DATA_FILE = "buku.json"

# --------- Data Handler ---------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# --------- Aplikasi ---------
class BukuTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Tracker Buku Bacaan")
        self.root.geometry("800x500")

        self.data = load_data()
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        frame_form = tk.Frame(self.root)
        frame_form.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_form, text="Judul:").grid(row=0, column=0)
        self.entry_judul = tk.Entry(frame_form)
        self.entry_judul.grid(row=0, column=1, padx=5)

        tk.Label(frame_form, text="Penulis:").grid(row=0, column=2)
        self.entry_penulis = tk.Entry(frame_form)
        self.entry_penulis.grid(row=0, column=3, padx=5)

        tk.Label(frame_form, text="Tahun:").grid(row=1, column=0)
        self.entry_tahun = tk.Entry(frame_form)
        self.entry_tahun.grid(row=1, column=1, padx=5)

        tk.Label(frame_form, text="Status:").grid(row=1, column=2)
        self.combo_status = ttk.Combobox(frame_form, values=["Belum Dibaca", "Selesai"])
        self.combo_status.grid(row=1, column=3, padx=5)
        self.combo_status.set("Belum Dibaca")

        self.btn_tambah = tk.Button(frame_form, text="➕ Tambah", command=self.tambah_buku)
        self.btn_tambah.grid(row=0, column=4, rowspan=2, padx=10)

        frame_table = tk.Frame(self.root)
        frame_table.pack(fill="both", expand=True, padx=10)

        columns = ("judul", "penulis", "tahun", "status")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.isi_form)

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)

        self.btn_edit = tk.Button(frame_btn, text="✏️ Edit", command=self.edit_buku)
        self.btn_edit.pack(side="left", padx=5)

        self.btn_hapus = tk.Button(frame_btn, text="🗑️ Hapus", command=self.hapus_buku)
        self.btn_hapus.pack(side="left", padx=5)

        self.btn_tandai = tk.Button(frame_btn, text="✅ Tandai Selesai", command=self.tandai_selesai)
        self.btn_tandai.pack(side="left", padx=5)

    def tambah_buku(self):
        judul = self.entry_judul.get().strip()
        penulis = self.entry_penulis.get().strip()
        tahun = self.entry_tahun.get().strip()
        status = self.combo_status.get()

        if not judul or not penulis or not tahun:
            messagebox.showwarning("Peringatan", "Semua kolom harus diisi.")
            return

        try:
            int(tahun)
        except ValueError:
            messagebox.showerror("Error", "Tahun harus berupa angka.")
            return

        self.data.append({
            "judul": judul,
            "penulis": penulis,
            "tahun": tahun,
            "status": status
        })
        save_data(self.data)
        self.refresh_table()
        self.clear_form()

    def edit_buku(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        self.data[idx] = {
            "judul": self.entry_judul.get().strip(),
            "penulis": self.entry_penulis.get().strip(),
            "tahun": self.entry_tahun.get().strip(),
            "status": self.combo_status.get()
        }
        save_data(self.data)
        self.refresh_table()
        self.clear_form()

    def hapus_buku(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        if messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus buku ini?"):
            del self.data[idx]
            save_data(self.data)
            self.refresh_table()
            self.clear_form()

    def tandai_selesai(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        self.data[idx]['status'] = "Selesai"
        save_data(self.data)
        self.refresh_table()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, item in enumerate(self.data):
            self.tree.insert("", "end", iid=idx, values=(item['judul'], item['penulis'], item['tahun'], item['status']))

    def isi_form(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        buku = self.data[idx]
        self.entry_judul.delete(0, tk.END)
        self.entry_judul.insert(0, buku['judul'])
        self.entry_penulis.delete(0, tk.END)
        self.entry_penulis.insert(0, buku['penulis'])
        self.entry_tahun.delete(0, tk.END)
        self.entry_tahun.insert(0, buku['tahun'])
        self.combo_status.set(buku['status'])

    def clear_form(self):
        self.entry_judul.delete(0, tk.END)
        self.entry_penulis.delete(0, tk.END)
        self.entry_tahun.delete(0, tk.END)
        self.combo_status.set("Belum Dibaca")
        self.tree.selection_remove(self.tree.selection())

if __name__ == '__main__':
    root = tk.Tk()
    app = BukuTrackerApp(root)
    root.mainloop()
