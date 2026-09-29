"""A small image-based yes/no quiz game."""

from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "questions"

# Keep this list in the order you want the images to appear.
# Replace each filename and correct answer with your own question data.
QUESTIONS = [
    {"image": "question_1.png", "answer": "tak"},
    {"image": "question_2.png", "answer": "nie"},
    {"image": "question_3.png", "answer": "tak"},
    {"image": "question_4.png", "answer": "tak"},
    {"image": "question_5.png", "answer": "tak"},
    {"image": "question_6.png", "answer": "nie"},
]

BACKGROUND = "#eeeeee"
BUTTON_BLUE = "#000000"
BUTTON_HOVER = "#241b2b"
BUTTON_RED = "#f06464"
BUTTON_TEXT = "#cda7ff"
TEXT_COLOR = "#222222"
WIN_YELLOW = "#f2c500"


class QuizGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Gra: Tak czy Nie")
        self.root.geometry("900x700")
        self.root.minsize(520, 420)
        self.root.configure(bg=BACKGROUND)

        self.question_index = 0
        self.score = 0
        self.mistakes = 0
        self.current_image = None
        self.displayed_image = None
        self.resize_job = None
        self.locked = False

        self._build_ui()
        if not self._validate_questions():
            return
        self.root.bind("<Configure>", self._on_resize)
        self._show_question()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BACKGROUND)
        header.pack(fill="x", padx=18, pady=(14, 8))

        self.score_label = tk.Label(
            header,
            text="Wynik: 0",
            font=("Arial", 16, "bold"),
            bg=BACKGROUND,
            fg=TEXT_COLOR,
        )
        self.score_label.pack(side="left", anchor="nw")

        self.progress_label = tk.Label(
            header,
            text="",
            font=("Arial", 14),
            bg=BACKGROUND,
            fg=TEXT_COLOR,
        )
        self.progress_label.pack(side="right", anchor="ne")

        self.image_area = tk.Frame(self.root, bg=BACKGROUND)
        self.image_area.pack(fill="both", expand=True, padx=18, pady=8)

        self.image_label = tk.Label(self.image_area, bg=BACKGROUND)
        self.image_label.pack(fill="both", expand=True)

        self.button_row = tk.Frame(self.root, bg=BACKGROUND)
        self.button_row.pack(fill="x", padx=18, pady=(6, 22))

        self.answer_buttons = {}
        for answer in ("tak", "nie"):
            button = tk.Button(
                self.button_row,
                text=answer.capitalize(),
                command=lambda selected=answer: self._submit_answer(selected),
                font=("Arial", 16, "bold"),
                bg=BUTTON_BLUE,
                activebackground=BUTTON_HOVER,
                fg=BUTTON_TEXT,
                activeforeground=BUTTON_TEXT,
                disabledforeground=BUTTON_TEXT,
                relief="flat",
                padx=34,
                pady=12,
                cursor="hand2",
            )
            button.pack(side="left", expand=True, fill="x", padx=10)
            button.bind("<Enter>", lambda event, b=button: self._set_hover(b, True))
            button.bind("<Leave>", lambda event, b=button: self._set_hover(b, False))
            self.answer_buttons[answer] = button

    def _validate_questions(self):
        if len(QUESTIONS) != 6:
            messagebox.showerror("Błąd konfiguracji", "Lista musi zawierać dokładnie 6 pytań.")
            self.root.destroy()
            return False

        invalid_answers = [q["answer"] for q in QUESTIONS if q["answer"] not in ("tak", "nie")]
        missing_images = [q["image"] for q in QUESTIONS if not (IMAGE_DIR / q["image"]).is_file()]
        if invalid_answers or missing_images:
            details = []
            if invalid_answers:
                details.append("Poprawne odpowiedzi mogą mieć wartość 'tak' albo 'nie'.")
            if missing_images:
                names = "\n".join(f"• {name}" for name in missing_images)
                details.append(f"Brakuje obrazków w folderze questions:\n{names}")
            details.append("Zobacz README.md, aby skonfigurować grę.")
            messagebox.showerror("Nie można uruchomić gry", "\n\n".join(details))
            self.root.destroy()
            return False
        return True

    def _show_question(self):
        if self.question_index >= len(QUESTIONS):
            self._show_win_screen()
            return

        question = QUESTIONS[self.question_index]
        image_path = IMAGE_DIR / question["image"]
        try:
            self.current_image = Image.open(image_path).convert("RGB")
        except (OSError, ValueError) as error:
            messagebox.showerror("Błąd obrazka", f"Nie udało się otworzyć pliku:\n{image_path}\n\n{error}")
            self.root.destroy()
            return

        self.progress_label.config(text=f"Pytanie {self.question_index + 1} / {len(QUESTIONS)}")
        self.score_label.config(text=f"Wynik: {self.score}")
        self._render_image()
        self._reset_buttons()
        self.locked = False

    def _render_image(self):
        if self.current_image is None:
            return
        width = max(120, self.image_area.winfo_width() - 16)
        height = max(120, self.image_area.winfo_height() - 16)
        image = self.current_image.copy()
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.displayed_image = ImageTk.PhotoImage(image)
        self.image_label.config(image=self.displayed_image)

    def _on_resize(self, event):
        if event.widget != self.root or self.current_image is None:
            return
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(100, self._render_image)

    def _set_hover(self, button, hovering):
        if button.cget("bg") == BUTTON_RED:
            return
        button.config(bg=BUTTON_HOVER if hovering else BUTTON_BLUE)

    def _reset_buttons(self):
        for button in self.answer_buttons.values():
            button.config(bg=BUTTON_BLUE, state="normal")

    def _submit_answer(self, selected_answer):
        if self.locked:
            return
        self.locked = True
        for button in self.answer_buttons.values():
            button.config(state="disabled")

        selected_button = self.answer_buttons[selected_answer]
        if selected_answer == QUESTIONS[self.question_index]["answer"]:
            self.score += 1
            self.score_label.config(text=f"Wynik: {self.score}")
            self.root.after(250, self._advance_question)
            return

        self.score -= 1
        self.mistakes += 1
        self.score_label.config(text=f"Wynik: {self.score}")
        selected_button.config(bg=BUTTON_RED, activebackground=BUTTON_RED)

        if self.mistakes >= 2:
            self.root.after(600, self._show_game_over)
        else:
            self.root.after(600, self._advance_question)

    def _advance_question(self):
        self.question_index += 1
        self._show_question()

    def _show_game_over(self):
        self._show_end_screen("KONIEC GRY", "#d93030")

    def _show_win_screen(self):
        self._show_end_screen("WYGRAŁEŚ GRĘ", WIN_YELLOW)

    def _show_end_screen(self, title, color):
        for widget in self.root.winfo_children():
            widget.destroy()

        end_frame = tk.Frame(self.root, bg=BACKGROUND)
        end_frame.pack(fill="both", expand=True)

        tk.Label(
            end_frame,
            text=title,
            font=("Arial", 34, "bold"),
            bg=BACKGROUND,
            fg=color,
            wraplength=760,
            justify="center",
        ).pack(expand=True, pady=(80, 12))

        tk.Label(
            end_frame,
            text=f"Wynik końcowy: {self.score}",
            font=("Arial", 23, "bold"),
            bg=BACKGROUND,
            fg=TEXT_COLOR,
        ).pack(pady=10)

        tk.Button(
            end_frame,
            text="Zagraj ponownie",
            command=self._restart,
            font=("Arial", 15, "bold"),
            bg=BUTTON_BLUE,
            activebackground=BUTTON_HOVER,
            fg=BUTTON_TEXT,
            activeforeground=BUTTON_TEXT,
            relief="flat",
            padx=24,
            pady=10,
            cursor="hand2",
        ).pack(pady=(20, 70))

    def _restart(self):
        self.question_index = 0
        self.score = 0
        self.mistakes = 0
        self.current_image = None
        self.displayed_image = None
        self.locked = False
        for widget in self.root.winfo_children():
            widget.destroy()
        self._build_ui()
        self._show_question()


def main():
    root = tk.Tk()
    QuizGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
