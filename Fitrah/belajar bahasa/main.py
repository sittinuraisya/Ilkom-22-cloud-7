import tkinter as tk
from tkinter import messagebox
import json
import random

# Load data
with open("data/vocab.json", "r") as f:
    vocab = json.load(f)

# Global state
score = 0
current_word = {}

# Function to get random word
def next_word():
    global current_word
    current_word = random.choice(vocab)
    word_label.config(text=f"Terjemahkan: {current_word['indonesia']}")
    entry.delete(0, tk.END)

# Function to check answer
def check_answer():
    global score
    user_input = entry.get().strip().lower()
    correct = current_word['english'].lower()
    if user_input == correct:
        score_label.config(text=f"Skor: {score + 1}")
        messagebox.showinfo("Benar!", "Jawaban kamu benar 🎉")
        score += 1
    else:
        messagebox.showerror("Salah", f"Jawaban salah. Yang benar: {correct}")
    next_word()

# UI setup
root = tk.Tk()
root.title("Belajar Bahasa")
root.geometry("400x300")

score_label = tk.Label(root, text="Skor: 0", font=("Helvetica", 14))
score_label.pack(pady=10)

word_label = tk.Label(root, text="", font=("Helvetica", 18))
word_label.pack(pady=20)

entry = tk.Entry(root, font=("Helvetica", 16))
entry.pack(pady=10)

submit_btn = tk.Button(root, text="Cek Jawaban", command=check_answer)
submit_btn.pack(pady=10)

next_word()

root.mainloop()
