import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

KAMUS_FILE = "kamus.json"

# ------------------ Data Handler ------------------
def load_kamus():
    if os.path.exists(KAMUS_FILE):
        with open(KAMUS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_kamus(data):
    with open(KAMUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ------------------ Main App ------------------
class KamusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📖 Kamus Pintar")
        self.kamus = load_kamus()
        self.filtered = {}
        self.selected_kata = None

        self.setup_ui()
        self.refresh_listbox()

    def setup_ui(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top, text="Cari Kata:").pack(side="left")
        self.entry_cari = tk.Entry(frame_top)
        self.entry_cari.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_cari.bind("<KeyRelease>", lambda e: self.cari_kata())

        frame_list = tk.Frame(self.root)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(frame_list, font=("Arial", 12))
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.tampilkan_arti)

        scrollbar = tk.Scrollbar(frame_list, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        frame_detail = tk.LabelFrame(self.root, text="Detail Kata")
        frame_detail.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_detail, text="Kata:").pack(anchor="w")
        self.entry_kata = tk.Entry(frame_detail, font=("Arial", 12))
        self.entry_kata.pack(fill="x")

        tk.Label(frame_detail, text="Arti:").pack(anchor="w", pady=(5,0))
        self.text_arti = tk.Text(frame_detail, height=5, font=("Arial", 12))
        self.text_arti.pack(fill="both")

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)

        self.btn_tambah = tk.Button(frame_btn, text="➕ Tambah / Simpan", command=self.tambah_kata)
        self.btn_tambah.grid(row=0, column=0, padx=5)

        self.btn_hapus = tk.Button(frame_btn, text="🗑️ Hapus", command=self.hapus_kata)
        self.btn_hapus.grid(row=0, column=1, padx=5)

        self.btn_bersih = tk.Button(frame_btn, text="🔄 Bersihkan", command=self.bersihkan_form)
        self.btn_bersih.grid(row=0, column=2, padx=5)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        self.filtered = dict(sorted(self.kamus.items()))
        for kata in self.filtered:
            self.listbox.insert(tk.END, kata)

    def cari_kata(self):
        query = self.entry_cari.get().lower()
        self.listbox.delete(0, tk.END)
        self.filtered = {k:v for k,v in self.kamus.items() if query in k.lower()}
        for kata in sorted(self.filtered):
            self.listbox.insert(tk.END, kata)

    def tampilkan_arti(self, event):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            kata = self.listbox.get(idx)
            arti = self.filtered.get(kata, "")
            self.entry_kata.delete(0, tk.END)
            self.entry_kata.insert(0, kata)
            self.text_arti.delete("1.0", tk.END)
            self.text_arti.insert(tk.END, arti)
            self.selected_kata = kata

    def tambah_kata(self):
        kata = self.entry_kata.get().strip()
        arti = self.text_arti.get("1.0", tk.END).strip()

        if not kata or not arti:
            messagebox.showwarning("Peringatan", "Kata dan arti harus diisi.")
            return

        self.kamus[kata] = arti
        save_kamus(self.kamus)
        self.refresh_listbox()
        messagebox.showinfo("Sukses", f"Kata '{kata}' disimpan.")
        self.bersihkan_form()

    def hapus_kata(self):
        kata = self.entry_kata.get().strip()
        if kata in self.kamus:
            if messagebox.askyesno("Konfirmasi", f"Hapus kata '{kata}' dari kamus?"):
                del self.kamus[kata]
                save_kamus(self.kamus)
                self.refresh_listbox()
                self.bersihkan_form()

    def bersihkan_form(self):
        self.entry_kata.delete(0, tk.END)
        self.text_arti.delete("1.0", tk.END)
        self.listbox.selection_clear(0, tk.END)
        self.selected_kata = None

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("600x500")
    app = KamusApp(root)
    root.mainloop()
