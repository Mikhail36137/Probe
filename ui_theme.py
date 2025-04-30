import tkinter as tk
from tkinter import ttk

# Цветовая палитра: корпоративный "серый + синий"
PALETTE = {
    "bg":      "#d9d9d9",  # Основной фон (серый)
    "panel":   "#e5e5e5",  # Фон панелей (светлее серого)
    "white":   "#ffffff",  # Белый для карточек и таблиц
    "primary": "#1e88e5",  # Синий акцент для кнопок
    "danger":  "#b00020",  # Красный для кнопок удаления
    "text":    "#212121",  # Основной текст (тёмно-серый)
    "red":     "#e53935",  # Приглушённый красный для индикаторов
    "green":   "#43a047",  # Приглушённый зелёный для индикаторов
}

# Определение шрифтов для единообразия
FONT_BASE = ("Segoe UI", 9)        # Уменьшен до 9 для меньшей высоты
FONT_BOLD = ("Segoe UI", 9, "bold")  # Уменьшен до 9
FONT_TITLE = ("Segoe UI", 18, "bold")  # Шрифт для заголовков окна

# Единообразные отступы
PADDING = 10
BUTTON_PADDING = (10, 2)  # Уменьшены вертикальные отступы для компактности
ENTRY_PADDING = 2         # Уменьшены отступы для полей ввода

# Иконки для кнопок
ICON_ADD = None
ICON_DELETE = None

def load_icons(root: tk.Tk) -> None:
    """Загружает PNG-иконки для кнопок."""
    global ICON_ADD, ICON_DELETE
    try:
        ICON_ADD = tk.PhotoImage(file="icons/add.png")  # Предполагается наличие файла add.png
        ICON_DELETE = tk.PhotoImage(file="icons/delete.png")  # Предполагается наличие файла delete.png
    except tk.TclError as e:
        print(f"Ошибка загрузки иконок: {e}. Используются текстовые иконки.")

def apply(root: "tk.Tk | ttk.Widget") -> None:
    """Применяет тему ко всем элементам интерфейса."""
    root.configure(bg=PALETTE["bg"])
    style = ttk.Style()
    style.theme_use("clam")

    # Основные фреймы: задают общий фон приложения и панелей
    style.configure("Main.TFrame", background=PALETTE["bg"])
    style.configure("Panel.TFrame", background=PALETTE["panel"])

    # Заголовки: для основного заголовка приложения и секций
    style.configure("Title.TLabel", background=PALETTE["bg"],
                    foreground=PALETTE["text"], font=FONT_TITLE)
    style.configure("Section.TLabel", background=PALETTE["bg"],
                    foreground=PALETTE["text"], font=FONT_BOLD)
    style.configure("TLabel", background=PALETTE["white"],
                    foreground=PALETTE["text"], font=FONT_BASE)

    # Карточки / таблицы: для рамок вокруг таблиц и групп виджетов
    style.configure("Card.TLabelframe", background=PALETTE["white"],
                    borderwidth=1, relief="solid", padding=PADDING)
    style.configure("Card.TLabelframe.Label",
                    background=PALETTE["bg"], foreground=PALETTE["primary"],
                    font=FONT_BOLD)

    # Кнопки: основные стили для кнопок приложения
    style.configure("Accent.TButton",
                    font=FONT_BOLD,
                    padding=BUTTON_PADDING,
                    background=PALETTE["primary"],
                    foreground="white",
                    borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", "#1976d2")])

    style.configure("Ghost.TButton",
                    font=FONT_BASE,
                    padding=BUTTON_PADDING,
                    background=PALETTE["panel"],
                    foreground=PALETTE["text"],
                    borderwidth=0)

    style.configure("Danger.TButton",
                    font=FONT_BASE,
                    padding=BUTTON_PADDING,
                    background=PALETTE["white"],
                    foreground=PALETTE["danger"],
                    borderwidth=1,
                    relief="solid")

    # Поля ввода: для текстовых полей и выпадающих списков
    style.configure("TEntry",
                    font=FONT_BASE,
                    padding=ENTRY_PADDING,
                    fieldbackground=PALETTE["white"],
                    bordercolor=PALETTE["panel"],
                    relief="flat")

    style.configure("TCombobox",
                    font=FONT_BASE,
                    padding=ENTRY_PADDING,
                    fieldbackground=PALETTE["white"])

    # Treeview (таблицы): для отображения данных в таблицах
    style.configure("Treeview",
                    font=FONT_BASE,
                    rowheight=20,  # Уменьшена высота строк таблицы для компактности
                    background=PALETTE["white"],
                    fieldbackground=PALETTE["white"])
    style.map("Treeview",
              background=[("selected", "#bbdefb")])

def toggle_dark(app: "tk.Tk | ttk.Widget", *args) -> None:
    """Переключает между светлой и тёмной темой."""
    if app.theme_mode.get() == "dark":
        PALETTE.update(bg="#212121", panel="#424242",
                       white="#303030", text="#e0e0e0")
    else:
        PALETTE.update(bg="#d9d9d9", panel="#e5e5e5",
                       white="#ffffff", text="#212121")
    apply(app.root)