import tkinter as tk
from tkinter import ttk
from typing import Any

def build_owl(app: Any) -> None:
    """Создаёт вкладку для работы с Owl."""
    owl_frame = ttk.Frame(app.tab_owl, style="Main.TFrame", padding=15)
    owl_frame.pack(fill="both", expand=True)

    chat_frame = ttk.LabelFrame(owl_frame, text="Чат с Owl", style="Card.TLabelframe")
    chat_frame.pack(fill="both", expand=True)

    # Поле чата с возможностью выделения текста (только для чтения)
    app.chat_display = tk.Text(chat_frame, height=20, width=80)
    app.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
    app.chat_display.config(state="disabled")

    # Добавляем контекстное меню для копирования
    context_menu = tk.Menu(app.chat_display, tearoff=0)
    context_menu.add_command(label="Копировать", command=lambda: copy_selected_text(app))

    def show_context_menu(event):
        """Показывает контекстное меню при нажатии правой кнопкой мыши."""
        if app.chat_display.selection_get():
            context_menu.post(event.x_root, event.y_root)

    app.chat_display.bind("<Button-3>", show_context_menu)

    input_frame = ttk.Frame(chat_frame)
    input_frame.pack(fill="x", pady=5)

    app.chat_input = ttk.Entry(input_frame)
    app.chat_input.pack(side="left", fill="x", expand=True, padx=5)

    ttk.Button(input_frame, text="Отправить", style="Accent.TButton",
               command=lambda: owl_respond_command(app, app.chat_input.get())).pack(side="left", padx=5)

    # Кнопка "Копировать всё"
    ttk.Button(input_frame, text="Копировать всё", style="Ghost.TButton",
               command=lambda: copy_chat_content(app)).pack(side="left", padx=5)

    # Кнопки загрузки данных внизу справа
    buttons_frame = ttk.Frame(chat_frame)
    buttons_frame.pack(side="bottom", anchor="se", pady=5)
    ttk.Button(buttons_frame, text="Загрузить выписку", style="Ghost.TButton",
               command=lambda: app.owl_respond_command("загрузи выписку")).pack(side="right", padx=5)

def owl_respond_command(app: Any, command: str) -> None:
    """Обрабатывает команды, отправленные в Owl."""
    if not command:
        return
    app.chat_display.config(state="normal")
    app.chat_display.insert(tk.END, f"Вы: {command}\n")
    response = app.owl.generate_response(command)
    app.chat_display.insert(tk.END, f"Owl: {response}\n")
    app.chat_display.config(state="disabled")
    app.chat_display.see(tk.END)
    app.chat_input.delete(0, tk.END)

def copy_selected_text(app: Any) -> None:
    """Копирует выделенный текст из чата в буфер обмена."""
    try:
        selected_text = app.chat_display.selection_get()
        app.root.clipboard_clear()
        app.root.clipboard_append(selected_text)
        update_status(app, "Выделенный текст скопирован в буфер обмена")
    except tk.TclError:
        update_status(app, "Ошибка: выделите текст для копирования")

def copy_chat_content(app: Any) -> None:
    """Копирует весь текст из чата в буфер обмена."""
    app.chat_display.config(state="normal")
    content = app.chat_display.get(1.0, tk.END).strip()
    app.root.clipboard_clear()
    app.root.clipboard_append(content)
    app.chat_display.config(state="disabled")
    update_status(app, "Сообщения Owl скопированы в буфер обмена")