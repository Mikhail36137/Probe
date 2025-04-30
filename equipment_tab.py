import tkinter as tk
from tkinter import ttk, messagebox
import locale
from components import create_row
from utils import update_status, log_message
from typing import Any, List

def build_equipment(app: Any) -> None:
    """Создаёт вкладку для учёта оборудования."""
    locale.setlocale(locale.LC_ALL, '')
    equipment_frame = ttk.Frame(app.tab_equipment, padding=15)
    equipment_frame.pack(fill="both", expand=True)

    # Настройка стилей для единообразного фона
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    app.equipment_table_frame = ttk.LabelFrame(equipment_frame, text="Оборудование", padding=10)
    app.equipment_table_frame.pack(fill="both", expand=True)

    app.equipment_rows = []
    app.equipment_rows_state = []

    app.equipment_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Наименование", "Тип", "Количество", "Стоимость за ед., ₽", "Общая стоимость, ₽"]
    header_frame = ttk.Frame(app.equipment_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(5):
        app.equipment_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_equipment_row(app)

    _create_equipment_buttons(app)

def _create_equipment_buttons(app: Any) -> None:
    """Создаёт кнопки управления для вкладки оборудования."""
    if hasattr(app, 'equipment_button_frame'):
        app.equipment_button_frame.destroy()
    button_frame = ttk.Frame(app.equipment_table_frame)
    button_frame.grid(row=len(app.equipment_rows) + 1, column=0, sticky="ew", pady=5)
    app.equipment_button_frame = button_frame
    ttk.Button(button_frame, text="+ Добавить строку",
               command=lambda: add_equipment_row(app)).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Анализ",
               command=lambda: analyze_equipment(app)).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Настроить типы",
               command=lambda: app.open_settings("equipment_types")).pack(side="left", padx=5)

def add_equipment_row(app: Any) -> None:
    """Добавляет строку для оборудования."""
    if len(app.equipment_rows) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        return
    columns = [
        {"type": "entry"},
        {"type": "combobox", "values_key": "equipment_types"},
        {"type": "entry"},
        {"type": "entry"},
        {"type": "label"}
    ]
    row_idx = len(app.equipment_rows) + 1  # Индекс строки начинается с 1 (после заголовков)
    row = create_row(
        app.equipment_table_frame,
        columns,
        lambda r: add_equipment_data(app, r),
        lambda r: delete_equipment_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.equipment_rows.append(row)
    app.equipment_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()

def add_equipment_data(app: Any, row: List[Any]) -> None:
    """Добавляет данные об оборудовании."""
    try:
        name = row[0].get()
        if not name:
            messagebox.showerror("Ошибка", "Введите наименование оборудования.")
            return
        equipment_type = row[1].get()
        if not equipment_type:
            messagebox.showerror("Ошибка", "Выберите или введите тип оборудования.")
            return
        quantity = locale.atof(row[2].get() or '0')
        cost_per_unit = locale.atof(row[3].get() or '0')
        total_cost = quantity * cost_per_unit
        row[4].config(text=f"{total_cost:,.0f}")
        app.state.capital_data["assets"]["equipment"].append((name, equipment_type, quantity, cost_per_unit, total_cost))
        for state in app.equipment_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        if equipment_type not in app.state.settings["equipment_types"]:
            app.state.settings["equipment_types"].append(equipment_type)
            app.save_settings()
            for r in app.equipment_rows:
                r[1]["values"] = app.state.settings["equipment_types"]
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлено оборудование: {name}")
    except ValueError as e:
        log_message(f"Ошибка при добавлении оборудования: {e}", level="ERROR")
        messagebox.showerror("Ошибка", "Введите числовые значения для количества и стоимости.")
        update_status(app, "Ошибка: некорректные числовые значения")

def delete_equipment_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку оборудования."""
    name = row[0].get()
    app.state.capital_data["assets"]["equipment"] = [
        e for e in app.state.capital_data["assets"]["equipment"] if e[0] != name
    ]
    index = app.equipment_rows.index(row)
    app.equipment_rows.pop(index)
    app.equipment_rows_state.pop(index)
    for widget in app.equipment_table_frame.winfo_children():
        widget.destroy()

    app.equipment_rows.clear()
    app.equipment_rows_state.clear()
    app.equipment_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Наименование", "Тип", "Количество", "Стоимость за ед., ₽", "Общая стоимость, ₽"]
    header_frame = ttk.Frame(app.equipment_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(len(app.equipment_rows_state)):
        app.equipment_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_equipment_row(app)

    app.update_dashboard()
    app.update_tab_indicators()
    _create_equipment_buttons(app)
    update_status(app, f"Удалено оборудование: {name}")

def analyze_equipment(app: Any) -> None:
    """Запускает анализ оборудования через Owl."""
    try:
        app.owl_respond_command("проверь оборудование")
        update_status(app, "Запущен анализ оборудования")
    except Exception as e:
        log_message(f"Ошибка при запуске анализа оборудования: {e}", level="ERROR")
        update_status(app, f"Ошибка анализа оборудования: {e}")