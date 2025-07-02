import tkinter as tk
from tkinter import messagebox
import json
import random
import os

SOAL_FILE = "soal.json"

# ----------- DATA & UTILITAS -----------
def load_soal():
    if not os.path.exists(SOAL_FILE):
        return []
    with open(SOAL_FILE, 'r') as f:
        return json.load(f)

def simpan_soal(soal_baru):
    soal = load_soal()
    soal.append(soal_baru)
    with open(SOAL_FILE, 'w') as f:
        json.dump(soal, f, indent=2)

def acak_soal(soal):
    random.shuffle(soal)
    return soal

# ----------- APP GUI -----------
class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Aplikasi Kuis Interaktif")

        self.soal = acak_soal(load_soal())
        self.index = 0
        self.score = 0

        self.pertanyaan_label = tk.Label(root, text="", wraplength=500, font=("Arial", 14), justify="left")
        self.pertanyaan_label.pack(pady=20)

        self.var_jawaban = tk.StringVar()
        self.opsi_buttons = []
        for i in range(4):
            rb = tk.Radiobutton(root, text="", variable=self.var_jawaban, value="", font=("Arial", 12))
            rb.pack(anchor="w")
            self.opsi_buttons.append(rb)

        self.btn_next = tk.Button(root, text="Jawab", command=self.cek_jawaban)
        self.btn_next.pack(pady=10)

        self.frame_bawah = tk.Frame(root)
        self.frame_bawah.pack(pady=10)

        self.btn_tambah = tk.Button(self.frame_bawah, text="➕ Tambah Soal", command=self.buka_tambah_soal)
        self.btn_tambah.grid(row=0, column=0, padx=10)

        self.btn_reset = tk.Button(self.frame_bawah, text="🔁 Ulangi", command=self.reset_kuis)
        self.btn_reset.grid(row=0, column=1, padx=10)

        self.tampilkan_soal()

    def tampilkan_soal(self):
        if self.index < len(self.soal):
            soal = self.soal[self.index]
            self.pertanyaan_label.config(text=f"{self.index+1}. {soal['pertanyaan']}")
            self.var_jawaban.set(None)

            opsi = soal['opsi'][:]
            random.shuffle(opsi)

            for i in range(4):
                self.opsi_buttons[i].config(text=opsi[i], value=opsi[i])
        else:
            self.selesai()

    def cek_jawaban(self):
        jawaban = self.var_jawaban.get()
        if not jawaban:
            messagebox.showwarning("Peringatan", "Pilih salah satu jawaban.")
            return

        soal = self.soal[self.index]
        if jawaban == soal['jawaban']:
            self.score += 1

        self.index += 1
        self.tampilkan_soal()

    def selesai(self):
        for rb in self.opsi_buttons:
            rb.pack_forget()
        self.pertanyaan_label.config(text=f"🎉 Selesai! Skor kamu: {self.score}/{len(self.soal)}")
        self.btn_next.config(state="disabled")

    def reset_kuis(self):
        self.soal = acak_soal(load_soal())
        self.index = 0
        self.score = 0
        for rb in self.opsi_buttons:
            rb.pack(anchor="w")
        self.btn_next.config(state="normal")
        self.tampilkan_soal()

    def buka_tambah_soal(self):
        TambahSoalWindow(self.root)

# ----------- TAMBAH SOAL -----------
class TambahSoalWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("➕ Tambah Soal Baru")

        tk.Label(self.window, text="Pertanyaan:").pack(anchor="w")
        self.entry_pertanyaan = tk.Text(self.window, height=4, width=50)
        self.entry_pertanyaan.pack()

        self.opsi_vars = []
        self.opsi_entries = []
        for i in range(4):
            frame = tk.Frame(self.window)
            frame.pack(anchor="w")
            var = tk.StringVar()
            tk.Radiobutton(frame, variable=var, value="jawaban", command=lambda i=i: self.set_jawaban(i)).pack(side="left")
            entry = tk.Entry(frame, width=40)
            entry.pack(side="left", padx=5)
            self.opsi_entries.append(entry)
            self.opsi_vars.append(False)

        self.jawaban_index = None

        self.btn_simpan = tk.Button(self.window, text="Simpan Soal", command=self.simpan_soal)
        self.btn_simpan.pack(pady=10)

    def set_jawaban(self, index):
        self.jawaban_index = index

    def simpan_soal(self):
        pertanyaan = self.entry_pertanyaan.get("1.0", tk.END).strip()
        opsi = [entry.get().strip() for entry in self.opsi_entries]

        if not pertanyaan or any(o == "" for o in opsi):
            messagebox.showwarning("Peringatan", "Semua kolom harus diisi.")
            return

        if self.jawaban_index is None:
            messagebox.showwarning("Peringatan", "Pilih jawaban yang benar.")
            return

        soal_baru = {
            "pertanyaan": pertanyaan,
            "opsi": opsi,
            "jawaban": opsi[self.jawaban_index]
        }
        simpan_soal(soal_baru)
        messagebox.showinfo("Sukses", "Soal berhasil ditambahkan!")
        self.window.destroy()

# ----------- MAIN -----------
if __name__ == "__main__":
    if not os.path.exists(SOAL_FILE):
        with open(SOAL_FILE, 'w') as f:
            json.dump([], f)

    root = tk.Tk()
    root.geometry("600x500")
    app = QuizApp(root)
    root.mainloop()
