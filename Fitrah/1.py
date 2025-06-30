import tkinter as tk
import os

# Fungsi untuk memuat paragraf dari file teks
def load_paragraphs(filepath):
    paragraphs = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            raw_paragraphs = content.split("\n\n")
            for para in raw_paragraphs:
                clean = para.strip()
                if clean:
                    paragraphs.append(clean.replace("\n", " "))
    return paragraphs

# Fungsi untuk menampilkan paragraf berdasarkan indeks saat ini
def show_paragraph(index):
    if 0 <= index < len(paragraphs):
        text_box.config(state=tk.NORMAL)
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, paragraphs[index])
        text_box.config(state=tk.DISABLED)
        label_status.config(text=f"Paragraf {index + 1} dari {len(paragraphs)}")
    update_buttons(index)

# Fungsi tombol "Sebelumnya"
def prev_paragraph():
    global current_index
    if current_index > 0:
        current_index -= 1
        show_paragraph(current_index)

# Fungsi tombol "Berikutnya"
def next_paragraph():
    global current_index
    if current_index < len(paragraphs) - 1:
        current_index += 1
        show_paragraph(current_index)

# Update tombol agar tidak bisa diklik saat awal/akhir
def update_buttons(index):
    if index == 0:
        btn_prev.config(state=tk.DISABLED)
    else:
        btn_prev.config(state=tk.NORMAL)

    if index == len(paragraphs) - 1:
        btn_next.config(state=tk.DISABLED)
    else:
        btn_next.config(state=tk.NORMAL)

# Inisialisasi GUI
root = tk.Tk()
root.title("Aplikasi Bantu Membaca")
root.geometry("600x400")

frame_top = tk.Frame(root)
frame_top.pack(pady=10)

label_title = tk.Label(frame_top, text="Bantu Membaca", font=("Helvetica", 18, "bold"))
label_title.pack()

text_box = tk.Text(root, wrap=tk.WORD, font=("Arial", 14), height=10)
text_box.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
text_box.config(state=tk.DISABLED)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

btn_prev = tk.Button(frame_bottom, text="Sebelumnya", width=15, command=prev_paragraph)
btn_prev.grid(row=0, column=0, padx=10)

btn_next = tk.Button(frame_bottom, text="Berikutnya", width=15, command=next_paragraph)
btn_next.grid(row=0, column=1, padx=10)

label_status = tk.Label(root, text="Memuat...", font=("Helvetica", 10))
label_status.pack(pady=5)

# Muat teks
file_path = "teks/cerita.txt"
paragraphs = load_paragraphs(file_path)
current_index = 0

if paragraphs:
    show_paragraph(current_index)
else:
    text_box.config(state=tk.NORMAL)
    text_box.insert(tk.END, "Teks tidak ditemukan atau kosong.")
    text_box.config(state=tk.DISABLED)
    btn_prev.config(state=tk.DISABLED)
    btn_next.config(state=tk.DISABLED)
    label_status.config(text="Tidak ada teks")

# Jalankan aplikasi
root.mainloop()
