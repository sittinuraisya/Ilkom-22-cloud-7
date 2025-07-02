import tkinter as tk
from tkinter import ttk
import json
import os

# Fungsi load data JSON
def load_data(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# Tampilkan detail kerajinan
def tampilkan_detail(kerajinan):
    judul_var.set(kerajinan["judul"])
    text_langkah.config(state=tk.NORMAL)
    text_langkah.delete("1.0", tk.END)
    for i, langkah in enumerate(kerajinan["langkah"]):
        text_langkah.insert(tk.END, f"{i+1}. {langkah}\n")
    text_langkah.config(state=tk.DISABLED)

# Filter berdasarkan bahan
def cari_kerajinan():
    bahan_dicari = bahan_entry.get().lower().strip()
    hasil_listbox.delete(0, tk.END)
    if not bahan_dicari:
        return
    hasil = []
    for item in data:
        bahan_list = [b.lower() for b in item["bahan"]]
        if bahan_dicari in bahan_list:
            hasil.append(item)
            hasil_listbox.insert(tk.END, item["judul"])
    global hasil_filter
    hasil_filter = hasil

# Tampilkan ketika diklik
def klik_listbox(evt):
    w = evt.widget
    if not hasil_filter:
        return
    if w.curselection():
        index = int(w.curselection()[0])
        kerajinan = hasil_filter[index]
        tampilkan_detail(kerajinan)

# Inisialisasi root window
root = tk.Tk()
root.title("Aplikasi Ide Kerajinan Tangan")
root.geometry("700x500")
root.config(bg="#fff8f0")

# Judul aplikasi
judul_app = tk.Label(root, text="📦 Ide Kerajinan Tangan", font=("Helvetica", 18, "bold"), bg="#fff8f0")
judul_app.pack(pady=10)

# Frame input pencarian
frame_input = tk.Frame(root, bg="#fff8f0")
frame_input.pack(pady=5)

label_bahan = tk.Label(frame_input, text="Cari berdasarkan bahan: ", font=("Helvetica", 12), bg="#fff8f0")
label_bahan.pack(side=tk.LEFT, padx=5)

bahan_entry = tk.Entry(frame_input, width=30, font=("Helvetica", 12))
bahan_entry.pack(side=tk.LEFT, padx=5)

btn_cari = tk.Button(frame_input, text="Cari", command=cari_kerajinan)
btn_cari.pack(side=tk.LEFT, padx=5)

# Frame hasil dan detail
frame_main = tk.Frame(root, bg="#fff8f0")
frame_main.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# Listbox hasil
frame_list = tk.Frame(frame_main)
frame_list.pack(side=tk.LEFT, fill=tk.Y)

label_hasil = tk.Label(frame_list, text="Hasil Pencarian:", font=("Helvetica", 12, "bold"))
label_hasil.pack(pady=5)

hasil_listbox = tk.Listbox(frame_list, width=40, height=20, font=("Helvetica", 11))
hasil_listbox.pack()
hasil_listbox.bind('<<ListboxSelect>>', klik_listbox)

# Detail kerajinan
frame_detail = tk.Frame(frame_main)
frame_detail.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

judul_var = tk.StringVar()
judul_label = tk.Label(frame_detail, textvariable=judul_var, font=("Helvetica", 14, "bold"), wraplength=300, justify=tk.LEFT)
judul_label.pack(pady=5)

label_langkah = tk.Label(frame_detail, text="Langkah-langkah:", font=("Helvetica", 12))
label_langkah.pack()

text_langkah = tk.Text(frame_detail, height=15, font=("Helvetica", 11), wrap=tk.WORD)
text_langkah.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
text_langkah.config(state=tk.DISABLED)

# Muat data awal
data = load_data("data/kerajinan.json")
hasil_filter = []

# Jalankan aplikasi
root.mainloop()
