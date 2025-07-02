import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

FILE_NAME = "siswa_data.json"

class SiswaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📘 Aplikasi Manajemen Siswa")
        self.data = {}
        self.selected_id = None

        self.setup_ui()
        self.load_data()
        self.refresh_table()

    def setup_ui(self):
        frame_form = tk.LabelFrame(self.root, text="Form Siswa", padx=10, pady=10)
        frame_form.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_form, text="Nama Siswa").grid(row=0, column=0, sticky="w")
        self.entry_nama = tk.Entry(frame_form)
        self.entry_nama.grid(row=0, column=1, sticky="we", padx=5)

        tk.Label(frame_form, text="Kelas").grid(row=1, column=0, sticky="w")
        self.entry_kelas = tk.Entry(frame_form)
        self.entry_kelas.grid(row=1, column=1, sticky="we", padx=5)

        tk.Label(frame_form, text="Nilai").grid(row=2, column=0, sticky="w")
        self.entry_nilai = tk.Entry(frame_form)
        self.entry_nilai.grid(row=2, column=1, sticky="we", padx=5)

        self.btn_simpan = tk.Button(frame_form, text="💾 Simpan Data", command=self.simpan_data)
        self.btn_simpan.grid(row=3, column=0, columnspan=2, pady=10)

        frame_search = tk.Frame(self.root)
        frame_search.pack(padx=10, fill="x")

        tk.Label(frame_search, text="🔍 Cari Nama:").pack(side="left")
        self.entry_search = tk.Entry(frame_search)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_table())

        self.btn_reset = tk.Button(frame_search, text="🔄 Reset", command=self.reset_form)
        self.btn_reset.pack(side="right", padx=5)

        self.tree = ttk.Treeview(self.root, columns=("nama", "kelas", "nilai"), show="headings")
        self.tree.heading("nama", text="Nama")
        self.tree.heading("kelas", text="Kelas")
        self.tree.heading("nilai", text="Nilai")
        self.tree.pack(padx=10, pady=10, fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(padx=10, pady=5, fill="x")

        self.btn_edit = tk.Button(frame_btn, text="✏️ Edit", command=self.edit_data)
        self.btn_edit.pack(side="left")

        self.btn_hapus = tk.Button(frame_btn, text="🗑️ Hapus", command=self.hapus_data)
        self.btn_hapus.pack(side="left", padx=5)

    def load_data(self):
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open(FILE_NAME, "w") as f:
            json.dump(self.data, f, indent=2)

    def simpan_data(self):
        nama = self.entry_nama.get().strip()
        kelas = self.entry_kelas.get().strip()
        nilai = self.entry_nilai.get().strip()

        if not nama or not kelas or not nilai:
            messagebox.showwarning("Peringatan", "Semua kolom harus diisi.")
            return

        try:
            nilai = float(nilai)
        except:
            messagebox.showerror("Error", "Nilai harus berupa angka.")
            return

        if self.selected_id:
            self.data[self.selected_id] = {"nama": nama, "kelas": kelas, "nilai": nilai}
            messagebox.showinfo("Berhasil", "Data siswa berhasil diperbarui.")
        else:
            new_id = str(len(self.data) + 1)
            self.data[new_id] = {"nama": nama, "kelas": kelas, "nilai": nilai}
            messagebox.showinfo("Berhasil", "Data siswa ditambahkan.")

        self.save_data()
        self.reset_form()
        self.refresh_table()

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        keyword = self.entry_search.get().lower()
        for id_, val in self.data.items():
            if keyword in val["nama"].lower():
                self.tree.insert("", "end", iid=id_, values=(val["nama"], val["kelas"], val["nilai"]))

    def on_select(self, event):
        selected = self.tree.focus()
        if selected:
            self.selected_id = selected
            val = self.data[selected]
            self.entry_nama.delete(0, tk.END)
            self.entry_kelas.delete(0, tk.END)
            self.entry_nilai.delete(0, tk.END)

            self.entry_nama.insert(0, val["nama"])
            self.entry_kelas.insert(0, val["kelas"])
            self.entry_nilai.insert(0, val["nilai"])

    def edit_data(self):
        if not self.selected_id:
            messagebox.showinfo("Info", "Pilih data yang ingin diedit.")
            return
        self.simpan_data()

    def hapus_data(self):
        if not self.selected_id:
            messagebox.showinfo("Info", "Pilih data yang ingin dihapus.")
            return

        confirm = messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus data ini?")
        if confirm:
            del self.data[self.selected_id]
            self.save_data()
            self.reset_form()
            self.refresh_table()
            messagebox.showinfo("Berhasil", "Data siswa dihapus.")

    def reset_form(self):
        self.entry_nama.delete(0, tk.END)
        self.entry_kelas.delete(0, tk.END)
        self.entry_nilai.delete(0, tk.END)
        self.entry_search.delete(0, tk.END)
        self.selected_id = None
        self.refresh_table()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x500")
    app = SiswaApp(root)
    root.mainloop()
