import tkinter as tk
from tkinter import messagebox, ttk
import random
import json
import os
import time
import threading

SKOR_FILE = "skor_math.json"

LEVELS = {
    "Mudah": (1, 10),
    "Sedang": (10, 50),
    "Sulit": (50, 100)
}

class MathQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📘 Aplikasi Kuis Matematika")
        self.root.geometry("500x400")

        self.level = tk.StringVar(value="Mudah")
        self.soal = ""
        self.jawaban = 0
        self.skor = 0
        self.total_soal = 0
        self.timer_thread = None
        self.time_limit = 30
        self.waktu_tersisa = self.time_limit
        self.timer_running = False

        self.setup_ui()

    def setup_ui(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="Pilih Level:").pack(side="left")
        self.level_cb = ttk.Combobox(frame_top, textvariable=self.level, values=list(LEVELS.keys()), width=10)
        self.level_cb.pack(side="left", padx=5)

        self.btn_mulai = tk.Button(frame_top, text="▶ Mulai", command=self.mulai_kuis)
        self.btn_mulai.pack(side="left", padx=5)

        self.btn_reset = tk.Button(frame_top, text="🔁 Ulang", command=self.reset_kuis)
        self.btn_reset.pack(side="left", padx=5)

        self.soal_label = tk.Label(self.root, text="", font=("Arial", 16))
        self.soal_label.pack(pady=20)

        self.entry_jawaban = tk.Entry(self.root, font=("Arial", 14), width=10, justify="center")
        self.entry_jawaban.pack()
        self.entry_jawaban.bind("<Return>", lambda e: self.cek_jawaban())

        self.btn_jawab = tk.Button(self.root, text="Jawab", command=self.cek_jawaban)
        self.btn_jawab.pack(pady=10)

        self.label_timer = tk.Label(self.root, text="Waktu: 30", font=("Arial", 12))
        self.label_timer.pack()

        self.label_skor = tk.Label(self.root, text="Skor: 0 dari 0", font=("Arial", 12))
        self.label_skor.pack()

        self.btn_lihat_skor = tk.Button(self.root, text="📊 Lihat Riwayat Skor", command=self.lihat_skor)
        self.btn_lihat_skor.pack(pady=10)

    def mulai_kuis(self):
        self.skor = 0
        self.total_soal = 0
        self.waktu_tersisa = self.time_limit
        self.timer_running = True
        self.mulai_timer()
        self.next_soal()

    def reset_kuis(self):
        self.timer_running = False
        self.skor = 0
        self.total_soal = 0
        self.soal_label.config(text="")
        self.label_skor.config(text="Skor: 0 dari 0")
        self.label_timer.config(text="Waktu: 30")
        self.entry_jawaban.delete(0, tk.END)

    def buat_soal(self):
        batas = LEVELS[self.level.get()]
        a = random.randint(*batas)
        b = random.randint(*batas)
        operasi = random.choice(['+', '-', '*', '/'])

        if operasi == "/":
            b = random.randint(1, batas[1])
            a = b * random.randint(1, 10)
            self.jawaban = a // b
            soal = f"{a} / {b}"
        elif operasi == "*":
            self.jawaban = a * b
            soal = f"{a} * {b}"
        elif operasi == "-":
            if a < b: a, b = b, a
            self.jawaban = a - b
            soal = f"{a} - {b}"
        else:
            self.jawaban = a + b
            soal = f"{a} + {b}"
        return soal

    def next_soal(self):
        if not self.timer_running:
            return
        self.soal = self.buat_soal()
        self.soal_label.config(text=self.soal)
        self.entry_jawaban.delete(0, tk.END)
        self.total_soal += 1
        self.update_skor()

    def cek_jawaban(self):
        if not self.timer_running:
            return
        try:
            jawaban_user = int(self.entry_jawaban.get())
            if jawaban_user == self.jawaban:
                self.skor += 1
        except ValueError:
            pass
        self.next_soal()

    def mulai_timer(self):
        def update():
            while self.waktu_tersisa > 0 and self.timer_running:
                time.sleep(1)
                self.waktu_tersisa -= 1
                self.label_timer.config(text=f"Waktu: {self.waktu_tersisa}")
            self.timer_running = False
            self.selesai()
        threading.Thread(target=update, daemon=True).start()

    def selesai(self):
        self.soal_label.config(text=f"⏰ Waktu Habis! Skor akhir: {self.skor}/{self.total_soal}")
        self.label_skor.config(text=f"Skor akhir: {self.skor} dari {self.total_soal}")
        self.simpan_skor()

    def update_skor(self):
        self.label_skor.config(text=f"Skor: {self.skor} dari {self.total_soal}")

    def simpan_skor(self):
        data = []
        if os.path.exists(SKOR_FILE):
            with open(SKOR_FILE, 'r') as f:
                data = json.load(f)
        data.append({
            "level": self.level.get(),
            "skor": self.skor,
            "total": self.total_soal,
            "waktu": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(SKOR_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def lihat_skor(self):
        if not os.path.exists(SKOR_FILE):
            messagebox.showinfo("Info", "Belum ada riwayat skor.")
            return

        with open(SKOR_FILE, 'r') as f:
            data = json.load(f)

        win = tk.Toplevel(self.root)
        win.title("📊 Riwayat Skor")

        tree = ttk.Treeview(win, columns=("Level", "Skor", "Total", "Waktu"), show="headings")
        tree.heading("Level", text="Level")
        tree.heading("Skor", text="Skor")
        tree.heading("Total", text="Total")
        tree.heading("Waktu", text="Waktu")

        for item in data[-20:][::-1]:
            tree.insert("", "end", values=(item['level'], item['skor'], item['total'], item['waktu']))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == '__main__':
    root = tk.Tk()
    app = MathQuizApp(root)
    root.mainloop()
