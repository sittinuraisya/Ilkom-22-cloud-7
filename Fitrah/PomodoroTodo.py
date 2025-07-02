import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import time
import threading

DATA_FILE = "todo.json"

# ------------ DATA HANDLER ------------
def load_tugas():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tugas(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ------------ MAIN APP ------------
class PomodoroTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📝 Pomodoro + To-Do App")
        self.tugas = load_tugas()
        self.timer_running = False
        self.timer_thread = None
        self.timer_time = 25 * 60

        self.setup_ui()
        self.refresh_listbox()

    def setup_ui(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", padx=10, pady=5)

        self.entry_tugas = tk.Entry(frame_top, width=40)
        self.entry_tugas.pack(side="left", padx=(0, 5))

        self.btn_tambah = tk.Button(frame_top, text="➕ Tambah", command=self.tambah_tugas)
        self.btn_tambah.pack(side="left")

        frame_list = tk.Frame(self.root)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(frame_list, columns=("status"), show="headings")
        self.tree.heading("status", text="Tugas")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_item)

        frame_actions = tk.Frame(self.root)
        frame_actions.pack(pady=5)

        self.btn_selesai = tk.Button(frame_actions, text="✅ Tandai Selesai", command=self.tandai_selesai)
        self.btn_selesai.pack(side="left", padx=5)

        self.btn_hapus = tk.Button(frame_actions, text="🗑️ Hapus", command=self.hapus_tugas)
        self.btn_hapus.pack(side="left", padx=5)

        # Pomodoro Timer
        timer_frame = tk.LabelFrame(self.root, text="⏳ Pomodoro Timer", padx=10, pady=10)
        timer_frame.pack(padx=10, pady=10, fill="x")

        self.label_timer = tk.Label(timer_frame, text="25:00", font=("Arial", 24))
        self.label_timer.pack()

        control_frame = tk.Frame(timer_frame)
        control_frame.pack(pady=5)

        self.btn_mulai = tk.Button(control_frame, text="▶ Mulai", command=self.mulai_timer)
        self.btn_mulai.grid(row=0, column=0, padx=5)

        self.btn_reset = tk.Button(control_frame, text="🔄 Reset", command=self.reset_timer)
        self.btn_reset.grid(row=0, column=1, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_listbox(self):
        self.tree.delete(*self.tree.get_children())
        for idx, t in enumerate(self.tugas):
            text = f"{'[✓]' if t['selesai'] else '[ ]'} {t['nama']}"
            self.tree.insert("", "end", iid=idx, values=(text,))

    def tambah_tugas(self):
        nama = self.entry_tugas.get().strip()
        if nama:
            self.tugas.append({"nama": nama, "selesai": False})
            save_tugas(self.tugas)
            self.entry_tugas.delete(0, tk.END)
            self.refresh_listbox()
        else:
            messagebox.showwarning("Peringatan", "Nama tugas tidak boleh kosong!")

    def hapus_tugas(self):
        selected = self.tree.focus()
        if selected:
            idx = int(selected)
            del self.tugas[idx]
            save_tugas(self.tugas)
            self.refresh_listbox()
        else:
            messagebox.showinfo("Info", "Pilih tugas terlebih dahulu.")

    def tandai_selesai(self):
        selected = self.tree.focus()
        if selected:
            idx = int(selected)
            self.tugas[idx]['selesai'] = not self.tugas[idx]['selesai']
            save_tugas(self.tugas)
            self.refresh_listbox()
        else:
            messagebox.showinfo("Info", "Pilih tugas terlebih dahulu.")

    def select_item(self, event):
        pass

    def mulai_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_thread = threading.Thread(target=self.run_timer)
            self.timer_thread.start()

    def run_timer(self):
        sisa = self.timer_time
        while sisa >= 0 and self.timer_running:
            menit = sisa // 60
            detik = sisa % 60
            waktu = f"{menit:02}:{detik:02}"
            self.label_timer.config(text=waktu)
            time.sleep(1)
            sisa -= 1
        if self.timer_running:
            self.label_timer.config(text="Waktu Habis!")
            messagebox.showinfo("⏰ Waktu Habis", "Waktu Pomodoro selesai! Saatnya istirahat.")
        self.timer_running = False

    def reset_timer(self):
        self.timer_running = False
        self.timer_time = 25 * 60
        self.label_timer.config(text="25:00")

    def on_close(self):
        self.timer_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("500x600")
    app = PomodoroTodoApp(root)
    root.mainloop()
