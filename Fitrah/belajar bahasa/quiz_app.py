import tkinter as tk
from tkinter import messagebox

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Aplikasi Kuis Interaktif")
        self.root.geometry("600x400")
        self.score = 0
        self.index = 0
        self.questions = self.load_questions()
        self.user_answers = []

        self.question_label = tk.Label(root, text="", wraplength=500, font=("Arial", 14), justify="left")
        self.question_label.pack(pady=20)

        self.var_choice = tk.StringVar()

        self.choices = []
        for _ in range(4):
            rb = tk.Radiobutton(root, text="", variable=self.var_choice, value="", font=("Arial", 12))
            rb.pack(anchor="w", padx=30)
            self.choices.append(rb)

        self.btn_next = tk.Button(root, text="Selanjutnya", command=self.next_question)
        self.btn_next.pack(pady=20)

        self.show_question()

    def load_questions(self):
        return [
            {
                "question": "Apa ibu kota Indonesia?",
                "options": ["Jakarta", "Bandung", "Surabaya", "Yogyakarta"],
                "answer": "Jakarta"
            },
            {
                "question": "Berapa hasil dari 15 x 3?",
                "options": ["45", "30", "60", "90"],
                "answer": "45"
            },
            {
                "question": "Siapa penemu lampu pijar?",
                "options": ["Einstein", "Edison", "Newton", "Tesla"],
                "answer": "Edison"
            },
            {
                "question": "Apa simbol kimia dari air?",
                "options": ["H2O", "O2", "CO2", "HO"],
                "answer": "H2O"
            },
            {
                "question": "Apa warna primer?",
                "options": ["Merah, Hijau, Biru", "Merah, Kuning, Biru", "Hijau, Biru, Kuning", "Merah, Putih, Hitam"],
                "answer": "Merah, Kuning, Biru"
            },
        ]

    def show_question(self):
        self.var_choice.set("")
        if self.index < len(self.questions):
            q = self.questions[self.index]
            self.question_label.config(text=f"Soal {self.index + 1}: {q['question']}")
            for i, opt in enumerate(q['options']):
                self.choices[i].config(text=opt, value=opt)
        else:
            self.show_result()

    def next_question(self):
        if not self.var_choice.get():
            messagebox.showwarning("Peringatan", "Pilih salah satu jawaban!")
            return

        correct_answer = self.questions[self.index]["answer"]
        user_answer = self.var_choice.get()
        self.user_answers.append(user_answer)

        if user_answer == correct_answer:
            self.score += 1

        self.index += 1
        self.show_question()

    def show_result(self):
        self.question_label.pack_forget()
        for rb in self.choices:
            rb.pack_forget()
        self.btn_next.pack_forget()

        result_frame = tk.Frame(self.root)
        result_frame.pack(pady=30)

        total = len(self.questions)
        tk.Label(result_frame, text=f"Skor Anda: {self.score} dari {total}", font=("Arial", 16)).pack(pady=10)

        review_btn = tk.Button(result_frame, text="🔍 Lihat Pembahasan", command=lambda: self.show_review(result_frame))
        review_btn.pack(pady=10)

        quit_btn = tk.Button(result_frame, text="Keluar", command=self.root.quit)
        quit_btn.pack()

    def show_review(self, parent_frame):
        parent_frame.destroy()
        review_frame = tk.Frame(self.root)
        review_frame.pack(padx=10, pady=10, fill="both", expand=True)

        canvas = tk.Canvas(review_frame)
        scrollbar = tk.Scrollbar(review_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, q in enumerate(self.questions):
            correct = q["answer"]
            user = self.user_answers[i]
            status = "✅ Benar" if user == correct else "❌ Salah"
            color = "green" if user == correct else "red"

            tk.Label(scroll_frame, text=f"Soal {i+1}: {q['question']}", font=("Arial", 12, "bold")).pack(anchor="w", pady=(5,0))
            tk.Label(scroll_frame, text=f"Jawaban Anda: {user}", fg=color).pack(anchor="w")
            tk.Label(scroll_frame, text=f"Jawaban Benar: {correct}", fg="blue").pack(anchor="w")
            tk.Label(scroll_frame, text=f"Status: {status}", fg=color).pack(anchor="w")
            tk.Label(scroll_frame, text="─"*60).pack()

        tk.Button(scroll_frame, text="Keluar", command=self.root.quit).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
