import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

FILE_NAME = "jadwal_data.json"

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]

class JadwalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📘 Aplikasi Jadwal Pelajaran")
        self.jadwal = {}
        self.selected_item = None

        self.load_data()
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        # Form Input
        frame_form = tk.Frame(self.root)
        frame_form.pack(pady=10)

        tk.Label(frame_form, text="Hari:").grid(row=0, column=0, padx=5)
        self.hari_cb = ttk.Combobox(frame_form, values=DAYS)
        self.hari_cb.grid(row=0, column=1, padx=5)

        tk.Label(frame_form, text="Mata Pelajaran:").grid(row=1, column=0, padx=5)
        self.mapel_entry = tk.Entry(frame_form)
        self.mapel_entry.grid(row=1, column=1, padx=5)

        tk.Label(frame_form, text="Jam (ex: 07.00-08.00):").grid(row=2, column=0, padx=5)
        self.jam_entry = tk.Entry(frame_form)
        self.jam_entry.grid(row=2, column=1, padx=5)

        self.btn_add = tk.Button(frame_form, text="Tambah / Simpan", command=self.tambah_jadwal)
        self.btn_add.grid(row=3, column=0, columnspan=2, pady=10)

        # Tabel Jadwal
        self.tree = ttk.Treeview(self.root, columns=("Hari", "Mapel", "Jam"), show="headings")
        self.tree.heading("Hari", text="Hari")
        self.tree.heading("Mapel", text="Mata Pelajaran")
        self.tree.heading("Jam", text="Jam")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_item)

        # Tombol edit & hapus
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=5)

        self.btn_edit = tk.Button(frame_btn, text="Edit", command=self.edit_jadwal)
        self.btn_edit.grid(row=0, column=0, padx=5)

        self.btn_delete = tk.Button(frame_btn, text="Hapus", command=self.hapus_jadwal)
        self.btn_delete.grid(row=0, column=1, padx=5)

    def tambah_jadwal(self):
        hari = self.hari_cb.get()
        mapel = self.mapel_entry.get()
        jam = self.jam_entry.get()

        if not all([hari, mapel, jam]):
            messagebox.showwarning("Peringatan", "Semua data harus diisi.")
            return

        item = {"hari": hari, "mapel": mapel, "jam": jam}

        if self.selected_item:
            idx = self.tree.index(self.selected_item)
            self.jadwal[idx] = item
            self.selected_item = None
        else:
            self.jadwal[len(self.jadwal)] = item

        self.save_data()
        self.clear_form()
        self.refresh_table()

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for item in sorted(self.jadwal.values(), key=lambda x: DAYS.index(x["hari"])):
            self.tree.insert("", "end", values=(item["hari"], item["mapel"], item["jam"]))

    def select_item(self, event):
        item = self.tree.focus()
        if item:
            values = self.tree.item(item)["values"]
            self.hari_cb.set(values[0])
            self.mapel_entry.delete(0, tk.END)
            self.mapel_entry.insert(0, values[1])
            self.jam_entry.delete(0, tk.END)
            self.jam_entry.insert(0, values[2])
            self.selected_item = item

    def edit_jadwal(self):
        if not self.selected_item:
            messagebox.showinfo("Info", "Pilih jadwal yang ingin diedit.")
            return

        self.tambah_jadwal()

    def hapus_jadwal(self):
        if not self.selected_item:
            messagebox.showinfo("Info", "Pilih jadwal yang ingin dihapus.")
            return

        idx = self.tree.index(self.selected_item)
        del self.jadwal[idx]

        # Perbaiki index
        self.jadwal = {i: v for i, v in enumerate(self.jadwal.values())}

        self.selected_item = None
        self.save_data()
        self.clear_form()
        self.refresh_table()

    def clear_form(self):
        self.hari_cb.set("")
        self.mapel_entry.delete(0, tk.END)
        self.jam_entry.delete(0, tk.END)

    def load_data(self):
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r") as f:
                self.jadwal = json.load(f)
                self.jadwal = {int(k): v for k, v in self.jadwal.items()}

    def save_data(self):
        with open(FILE_NAME, "w") as f:
            json.dump(self.jadwal, f, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x500")
    app = JadwalApp(root)
    root.mainloop()
