import tkinter as tk
from tkinter import colorchooser
from tkinter import filedialog
from PIL import ImageGrab

class AplikasiMenggambar:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Menggambar Sederhana")

        self.canvas = tk.Canvas(root, bg="white", width=800, height=600)
        self.canvas.pack(padx=10, pady=10)

        self.warna = "black"
        self.ukuran_kuas = 5
        self.gambar_sedang = False

        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack()

        self.btn_warna = tk.Button(toolbar, text="Pilih Warna", command=self.pilih_warna)
        self.btn_warna.pack(side=tk.LEFT, padx=5)

        self.ukuran_var = tk.IntVar(value=self.ukuran_kuas)
        self.ukuran_slider = tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL,
                                      label="Ukuran Kuas", variable=self.ukuran_var)
        self.ukuran_slider.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(toolbar, text="Bersihkan", command=self.bersihkan_canvas)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.btn_simpan = tk.Button(toolbar, text="Simpan Gambar", command=self.simpan_gambar)
        self.btn_simpan.pack(side=tk.LEFT, padx=5)

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.mulai_gambar)
        self.canvas.bind("<B1-Motion>", self.gambar)
        self.canvas.bind("<ButtonRelease-1>", self.selesai_gambar)

    def pilih_warna(self):
        warna_baru = colorchooser.askcolor(color=self.warna)[1]
        if warna_baru:
            self.warna = warna_baru

    def mulai_gambar(self, event):
        self.gambar_sedang = True
        self.x_prev = event.x
        self.y_prev = event.y

    def gambar(self, event):
        if self.gambar_sedang:
            self.ukuran_kuas = self.ukuran_var.get()
            self.canvas.create_line(
                self.x_prev, self.y_prev, event.x, event.y,
                fill=self.warna, width=self.ukuran_kuas,
                capstyle=tk.ROUND, smooth=True
            )
            self.x_prev = event.x
            self.y_prev = event.y

    def selesai_gambar(self, event):
        self.gambar_sedang = False

    def bersihkan_canvas(self):
        self.canvas.delete("all")

    def simpan_gambar(self):
        # Ambil posisi relatif window di layar
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()

        # Ambil screenshot dan simpan
        try:
            image = ImageGrab.grab().crop((x, y, x1, y1))
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png")])
            if file_path:
                image.save(file_path)
                print("✅ Gambar berhasil disimpan.")
        except Exception as e:
            print("❌ Gagal menyimpan gambar:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = AplikasiMenggambar(root)
    root.mainloop()
