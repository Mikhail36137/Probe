import tkinter as tk
from tkinter import ttk

def create_scrollable_expense_block(parent, title, columns):
    # === Обёртка блока ===
    group = ttk.LabelFrame(parent, text=title)
    group.pack(side='left', fill='both', expand=True, padx=10, pady=10)

    # === Контейнер: Canvas + Scrollbar ===
    container = ttk.Frame(group)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, height=200, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # === Внутренний фрейм ===
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="inner_frame")
    canvas.configure(yscrollcommand=scrollbar.set)

    # === Растягиваем scrollable_frame ===
    def on_canvas_configure(event):
        canvas.itemconfig("inner_frame", width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)

    # === Заголовки + растяжение колонок ===
    for idx, header in enumerate(columns):
        scrollable_frame.grid_columnconfigure(idx, weight=1)
        ttk.Label(scrollable_frame, text=header).grid(row=0, column=idx, padx=5, pady=3, sticky="ew")

    entries = []

    # === Добавление строки ===
    def add_row():
        row_idx = len(entries) + 1
        row_entries = []
        for i in range(len(columns)):
            if columns[i] == "Категория":
                cb = ttk.Combobox(scrollable_frame, values=["Аренда", "Зарплата", "Прочее"])
                cb.grid(row=row_idx, column=i, padx=5, pady=2, sticky="ew")
                row_entries.append(cb)
            elif columns[i] == "Контрагент":
                cb = ttk.Combobox(scrollable_frame, values=["Поставщик 1", "Поставщик 2"])
                cb.grid(row=row_idx, column=i, padx=5, pady=2, sticky="ew")
                row_entries.append(cb)
            else:
                e = ttk.Entry(scrollable_frame)
                e.grid(row=row_idx, column=i, padx=5, pady=2, sticky="ew")
                row_entries.append(e)
        entries.append(row_entries)

    # === Кнопка добавления строки ===
    add_button = ttk.Button(group, text="+ Добавить строку", command=add_row)
    add_button.pack(pady=5)

    add_row()  # Первая строка

    return entries

# ======== Главное окно ========
root = tk.Tk()
root.title("PulseBoard Pro: Умная Ревизия")
root.geometry("1200x600")
root.configure(bg="#d9d9d9")

# ======== Стили ttk ========
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#d9d9d9")
style.configure("TLabel", background="#d9d9d9")
style.configure("TLabelFrame", background="#d9d9d9")
style.configure("TButton", background="#d9d9d9")

# ======== Верх: расходы ========
top_frame = ttk.Frame(root)
top_frame.pack(fill='both', expand=True, padx=10, pady=10)

create_scrollable_expense_block(top_frame, "Безналичные расходы", ["Категория", "Контрагент", "Сумма, ₽"])
create_scrollable_expense_block(top_frame, "Наличные расходы", ["Категория", "Сумма, ₽"])

# ======== Низ: Баланс наличных ========
bottom_frame = ttk.LabelFrame(root, text="Баланс наличных", padding=10)
bottom_frame.pack(fill='x', padx=10, pady=(0, 10))

ttk.Label(bottom_frame, text="Начальный остаток на 23.03.2025, ₽:").grid(row=0, column=0, sticky='w', pady=3)
start_entry = ttk.Entry(bottom_frame, width=20)
start_entry.grid(row=0, column=1, padx=5)

ttk.Label(bottom_frame, text="Поступления с 23.03.2025 по 26.03.2025, ₽:").grid(row=1, column=0, sticky='w', pady=3)
income_entry = ttk.Entry(bottom_frame, width=20)
income_entry.grid(row=1, column=1, padx=5)

add_button = ttk.Button(bottom_frame, text="Добавить")
add_button.grid(row=0, column=2, rowspan=2, padx=10)

root.mainloop()
