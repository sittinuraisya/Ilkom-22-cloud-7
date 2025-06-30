import tkinter as tk
import json
import os

# Fungsi untuk memuat resep dari file
def load_recipes(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)

# Menampilkan resep berdasarkan indeks
def show_recipe(index):
    global current_index
    if 0 <= index < len(recipes):
        current_index = index
        recipe = recipes[index]
        title_label.config(text=recipe['nama'])

        # Tampilkan bahan
        text_bahan.config(state=tk.NORMAL)
        text_bahan.delete("1.0", tk.END)
        for b in recipe['bahan']:
            text_bahan.insert(tk.END, f"• {b}\n")
        text_bahan.config(state=tk.DISABLED)

        # Tampilkan langkah
        text_langkah.config(state=tk.NORMAL)
        text_langkah.delete("1.0", tk.END)
        for i, l in enumerate(recipe['langkah']):
            text_langkah.insert(tk.END, f"{i+1}. {l}\n")
        text_langkah.config(state=tk.DISABLED)

        # Update status
        label_status.config(text=f"Resep {index+1} dari {len(recipes)}")

        update_buttons()

# Tombol sebelumnya
def prev_recipe():
    if current_index > 0:
        show_recipe(current_index - 1)

# Tombol berikutnya
def next_recipe():
    if current_index < len(recipes) - 1:
        show_recipe(current_index + 1)

# Atur status tombol
def update_buttons():
    if current_index == 0:
        btn_prev.config(state=tk.DISABLED)
    else:
        btn_prev.config(state=tk.NORMAL)

    if current_index == len(recipes) - 1:
        btn_next.config(state=tk.DISABLED)
    else:
        btn_next.config(state=tk.NORMAL)

# Buat jendela utama
root = tk.Tk()
root.title("Aplikasi Memasak")
root.geometry("700x500")
root.configure(bg="#fefae0")

# Judul resep
title_label = tk.Label(root, text="Judul Resep", font=("Helvetica", 20, "bold"), bg="#fefae0")
title_label.pack(pady=10)

# Frame utama
main_frame = tk.Frame(root, bg="#fefae0")
main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

# Frame bahan
frame_bahan = tk.Frame(main_frame, bg="#faedcd", bd=2, relief=tk.GROOVE)
frame_bahan.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

label_bahan = tk.Label(frame_bahan, text="Bahan-Bahan", font=("Helvetica", 14, "bold"), bg="#faedcd")
label_bahan.pack(pady=5)

text_bahan = tk.Text(frame_bahan, wrap=tk.WORD, height=10, font=("Arial", 12))
text_bahan.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
text_bahan.config(state=tk.DISABLED)

# Frame langkah
frame_langkah = tk.Frame(main_frame, bg="#d4a373", bd=2, relief=tk.GROOVE)
frame_langkah.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

label_langkah = tk.Label(frame_langkah, text="Langkah-Langkah", font=("Helvetica", 14, "bold"), bg="#d4a373")
label_langkah.pack(pady=5)

text_langkah = tk.Text(frame_langkah, wrap=tk.WORD, height=10, font=("Arial", 12))
text_langkah.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
text_langkah.config(state=tk.DISABLED)

# Navigasi bawah
frame_bawah = tk.Frame(root, bg="#fefae0")
frame_bawah.pack(pady=10)

btn_prev = tk.Button(frame_bawah, text="<< Sebelumnya", command=prev_recipe, width=15)
btn_prev.pack(side=tk.LEFT, padx=20)

label_status = tk.Label(frame_bawah, text="Status", font=("Arial", 10), bg="#fefae0")
label_status.pack(side=tk.LEFT)

btn_next = tk.Button(frame_bawah, text="Berikutnya >>", command=next_recipe, width=15)
btn_next.pack(side=tk.LEFT, padx=20)

# Muat data resep
recipes = load_recipes("data/resep.json")
current_index = 0

if recipes:
    show_recipe(current_index)
else:
    title_label.config(text="Tidak ada resep ditemukan.")
    text_bahan.insert(tk.END, "Silakan tambahkan resep ke dalam 'data/resep.json'")
    text_bahan.config(state=tk.DISABLED)
    text_langkah.insert(tk.END, "Silakan tambahkan resep ke dalam 'data/resep.json'")
    text_langkah.config(state=tk.DISABLED)
    btn_prev.config(state=tk.DISABLED)
    btn_next.config(state=tk.DISABLED)
    label_status.config(text="Tidak ada resep")

root.mainloop()
