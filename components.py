import tkinter as tk
from tkinter import ttk
from ui_theme import ICON_ADD, ICON_DELETE

def create_row(
    parent: ttk.Frame,
    columns: list,
    add_callback: callable,
    delete_callback: callable,
    settings: dict,
    row_idx: int,
) -> list:
    """Создаёт строку ввода с полями и кнопками."""
    row_frame = ttk.Frame(parent)
    row_frame.grid(row=row_idx, column=0, columnspan=len(columns)+2, sticky="ew", padx=5, pady=2)
    row = []

    # Настройка веса колонок для равномерного растяжения
    for i in range(len(columns) + 2):  # +2 для кнопок
        row_frame.grid_columnconfigure(i, weight=1 if i < len(columns) else 0)

    for i, col in enumerate(columns):
        if col["type"] == "combobox":
            values_key = col.get("values_key", "")
            cb = ttk.Combobox(row_frame, values=settings.get(values_key, []))
            cb.grid(row=0, column=i, padx=5, pady=2, sticky="ew")
            row.append(cb)
        elif col["type"] == "entry":
            e = ttk.Entry(row_frame)
            e.grid(row=0, column=i, padx=5, pady=2, sticky="ew")
            row.append(e)
        elif col["type"] == "label":
            l = ttk.Label(row_frame, text="0")
            l.grid(row=0, column=i, padx=5, pady=2, sticky="ew")
            row.append(l)

    # Кнопка "Добавить" с PNG-иконкой
    add_btn = ttk.Button(
        row_frame,
        image=ICON_ADD if ICON_ADD else None,
        text="➕" if not ICON_ADD else "",
        style="Ghost.TButton",
        command=lambda: add_callback(row)
    )
    add_btn.grid(row=0, column=len(columns), padx=2, sticky="ew")

    # Кнопка "Удалить" с PNG-иконкой
    delete_btn = ttk.Button(
        row_frame,
        image=ICON_DELETE if ICON_DELETE else None,
        text="🗑" if not ICON_DELETE else "",
        style="Danger.TButton",
        command=lambda: delete_callback(row)
    )
    delete_btn.grid(row=0, column=len(columns) + 1, padx=2, sticky="ew")

    indicator = ttk.Label(row_frame, text="  ", background="red", width=2)
    indicator.grid(row=0, column=len(columns) + 2, padx=2)

    row.append(indicator)
    return row