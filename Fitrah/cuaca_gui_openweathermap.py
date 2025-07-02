import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
import io
import threading
import time

API_KEY = "MASUKKAN_API_KEY_ANDA_DI_SINI"

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikasi Cuaca")
        self.geometry("400x600")
        self.resizable(False, False)
        self.configure(bg="#a7c0dc")

        self.city_name = tk.StringVar()
        self.weather_data = {}

        self.create_widgets()
        self.update_clock()

    def create_widgets(self):
        # Judul
        self.label_title = tk.Label(self, text="Aplikasi Cuaca", font=("Helvetica", 20, "bold"), bg="#a7c0dc")
        self.label_title.pack(pady=10)

        # Input kota
        self.entry_city = tk.Entry(self, textvariable=self.city_name, font=("Helvetica", 14), width=25)
        self.entry_city.pack(pady=10)

        # Tombol cari
        self.button_get = tk.Button(self, text="Cari Cuaca", command=self.get_weather, font=("Helvetica", 12), bg="#4a90e2", fg="white")
        self.button_get.pack(pady=5)

        # Label hasil
        self.label_city = tk.Label(self, text="", font=("Helvetica", 16, "bold"), bg="#a7c0dc")
        self.label_city.pack(pady=10)

        self.weather_icon_label = tk.Label(self, bg="#a7c0dc")
        self.weather_icon_label.pack()

        self.label_temp = tk.Label(self, text="", font=("Helvetica", 16), bg="#a7c0dc")
        self.label_temp.pack()

        self.label_desc = tk.Label(self, text="", font=("Helvetica", 14), bg="#a7c0dc")
        self.label_desc.pack()

        self.label_humidity = tk.Label(self, text="", font=("Helvetica", 12), bg="#a7c0dc")
        self.label_humidity.pack()

        self.label_time = tk.Label(self, text="", font=("Helvetica", 10), bg="#a7c0dc")
        self.label_time.pack(pady=10)

        self.refresh_label = tk.Label(self, text="Auto refresh 10 detik", font=("Helvetica", 8), bg="#a7c0dc")
        self.refresh_label.pack()

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.label_time.configure(text=f"Jam: {now}")
        self.after(1000, self.update_clock)

    def get_weather(self):
        city = self.city_name.get()
        if not city:
            messagebox.showwarning("Peringatan", "Masukkan nama kota terlebih dahulu.")
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=id"
        try:
            response = requests.get(url)
            data = response.json()

            if data.get("cod") != 200:
                self.label_city.config(text="Kota tidak ditemukan")
                self.clear_labels()
                return

            self.weather_data = {
                "city": data["name"],
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"].capitalize(),
                "icon": data["weather"][0]["icon"]
            }

            self.update_weather_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengambil data: {e}")

    def update_weather_ui(self):
        self.label_city.config(text=self.weather_data["city"])
        self.label_temp.config(text=f"Suhu: {self.weather_data['temp']}°C")
        self.label_desc.config(text=f"Cuaca: {self.weather_data['description']}")
        self.label_humidity.config(text=f"Kelembapan: {self.weather_data['humidity']}%")

        # Ambil dan tampilkan ikon cuaca
        icon_url = f"http://openweathermap.org/img/wn/{self.weather_data['icon']}@2x.png"
        try:
            icon_data = requests.get(icon_url).content
            image = Image.open(io.BytesIO(icon_data))
            image = image.resize((100, 100), Image.ANTIALIAS)
            icon = ImageTk.PhotoImage(image)
            self.weather_icon_label.config(image=icon)
            self.weather_icon_label.image = icon
        except:
            pass

    def clear_labels(self):
        self.label_temp.config(text="")
        self.label_desc.config(text="")
        self.label_humidity.config(text="")
        self.weather_icon_label.config(image=None)
        self.weather_icon_label.image = None

    def auto_refresh(self):
        while True:
            if self.city_name.get():
                self.get_weather()
            time.sleep(10)

if __name__ == "__main__":
    app = WeatherApp()
    # Thread untuk auto-refresh
    threading.Thread(target=app.auto_refresh, daemon=True).start()
    app.mainloop()
