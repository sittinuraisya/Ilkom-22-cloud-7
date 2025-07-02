import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json

FILE_NAME = "notes_data.json"

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📝 Aplikasi Catatan")
        self.notes = {}
        self.selected_note = None

        self.load_notes()
        self.setup_ui()
        self.refresh_listbox()

    def setup_ui(self):
        self.frame_left = tk.Frame(self.root)
        self.frame_left.pack(side=tk.LEFT, padx=10, pady=10)

        self.frame_right = tk.Frame(self.root)
        self.frame_right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.label_list = tk.Label(self.frame_left, text="📑 Daftar Catatan:")
        self.label_list.pack()

        self.listbox = tk.Listbox(self.frame_left, height=20, width=30)
        self.listbox.pack()
        self.listbox.bind('<<ListboxSelect>>', self.select_note)

        self.btn_new = tk.Button(self.frame_left, text="🆕 Buat Catatan Baru", command=self.create_note)
        self.btn_new.pack(pady=5)

        self.btn_delete = tk.Button(self.frame_left, text="🗑️ Hapus Catatan", command=self.delete_note)
        self.btn_delete.pack(pady=5)

        self.label_title = tk.Label(self.frame_right, text="Judul")
        self.label_title.pack()

        self.entry_title = tk.Entry(self.frame_right, font=('Arial', 14))
        self.entry_title.pack(fill=tk.X)

        self.label_content = tk.Label(self.frame_right, text="Isi Catatan:")
        self.label_content.pack()

        self.text_content = tk.Text(self.frame_right, wrap=tk.WORD, font=('Arial', 12))
        self.text_content.pack(fill=tk.BOTH, expand=True)

        self.btn_save = tk.Button(self.frame_right, text="💾 Simpan Catatan", command=self.save_note)
        self.btn_save.pack(pady=5)

    def load_notes(self):
        if os.path.exists(FILE_NAME):
            try:
                with open(FILE_NAME, 'r') as file:
                    self.notes = json.load(file)
            except:
                self.notes = {}

    def save_notes_to_file(self):
        with open(FILE_NAME, 'w') as file:
            json.dump(self.notes, file, indent=2)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for title in self.notes.keys():
            self.listbox.insert(tk.END, title)

    def create_note(self):
        title = simpledialog.askstring("Catatan Baru", "Masukkan judul catatan:")
        if title:
            if title in self.notes:
                messagebox.showwarning("Peringatan", "Catatan dengan judul ini sudah ada.")
            else:
                self.notes[title] = ""
                self.refresh_listbox()
                self.listbox.selection_clear(0, tk.END)
                idx = list(self.notes.keys()).index(title)
                self.listbox.selection_set(idx)
                self.select_note(None)

    def delete_note(self):
        if not self.selected_note:
            messagebox.showinfo("Info", "Pilih catatan yang akan dihapus.")
            return
        confirm = messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus '{self.selected_note}'?")
        if confirm:
            del self.notes[self.selected_note]
            self.selected_note = None
            self.entry_title.delete(0, tk.END)
            self.text_content.delete("1.0", tk.END)
            self.refresh_listbox()
            self.save_notes_to_file()

    def select_note(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        title = self.listbox.get(idx)
        self.selected_note = title
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, title)
        self.text_content.delete("1.0", tk.END)
        self.text_content.insert("1.0", self.notes[title])

    def save_note(self):
        if not self.selected_note:
            messagebox.showinfo("Info", "Pilih catatan untuk disimpan.")
            return
        new_title = self.entry_title.get().strip()
        content = self.text_content.get("1.0", tk.END).strip()

        if new_title != self.selected_note:
            if new_title in self.notes:
                messagebox.showwarning("Peringatan", "Judul catatan sudah digunakan.")
                return
            self.notes[new_title] = content
            del self.notes[self.selected_note]
            self.selected_note = new_title
        else:
            self.notes[self.selected_note] = content

        self.save_notes_to_file()
        self.refresh_listbox()
        messagebox.showinfo("Berhasil", "Catatan disimpan.")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("700x500")
    app = NotesApp(root)
    root.mainloop()
