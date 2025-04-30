import tkinter as tk
from tkinter import ttk, messagebox
import locale
from datetime import datetime
from components import create_row
from utils import update_status, log_message
from typing import Any, List

def build_creditors(app: Any) -> None:
    """Создаёт вкладку для управления кредиторской задолженностью."""
    locale.setlocale(locale.LC_ALL, '')
    creditors_frame = ttk.Frame(app.tab_creditors, padding=15)
    creditors_frame.pack(fill="both", expand=True)

    # Настройка стилей для единообразного фона
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    app.creditors_table_frame = ttk.LabelFrame(creditors_frame, text="Кредиторы", padding=10)
    app.creditors_table_frame.pack(fill="both", expand=True)

    app.creditors_rows = []
    app.creditors_rows_state = []

    app.creditors_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Поставщик", "Сумма (факт), ₽"]
    header_frame = ttk.Frame(app.creditors_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(5):
        app.creditors_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_creditors_row(app)

    _create_creditors_buttons(app)

def build_debtors(app: Any) -> None:
    """Создаёт вкладку для управления дебиторской задолженностью."""
    locale.setlocale(locale.LC_ALL, '')
    debtors_frame = ttk.Frame(app.tab_debtors, padding=15)
    debtors_frame.pack(fill="both", expand=True)

    # Настройка стилей для единообразного фона
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    app.debtors_table_frame = ttk.LabelFrame(debtors_frame, text="Дебиторы", padding=10)
    app.debtors_table_frame.pack(fill="both", expand=True)

    app.debtors_rows = []
    app.debtors_rows_state = []

    app.debtors_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Заказчик", "Сумма (факт), ₽"]
    header_frame = ttk.Frame(app.debtors_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(5):
        app.debtors_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_debtors_row(app)

    _create_debtors_buttons(app)

def _create_creditors_buttons(app: Any) -> None:
    """Создаёт кнопки управления для вкладки кредиторов."""
    if hasattr(app, 'creditors_button_frame'):
        app.creditors_button_frame.destroy()
    button_frame = ttk.Frame(app.creditors_table_frame)
    button_frame.grid(row=len(app.creditors_rows) + 1, column=0, sticky="ew", pady=5)
    button_frame.grid_columnconfigure((0, 1, 2), weight=1)
    app.creditors_button_frame = button_frame
    ttk.Button(button_frame, text="+ Добавить строку",
               command=lambda: add_creditors_row(app)).grid(row=0, column=0, sticky="ew", padx=5)
    ttk.Button(button_frame, text="Анализ",
               command=lambda: analyze_creditors(app)).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(button_frame, text="Настроить поставщиков",
               command=lambda: app.open_settings("suppliers")).grid(row=0, column=2, sticky="ew", padx=5)

def _create_debtors_buttons(app: Any) -> None:
    """Создаёт кнопки управления для вкладки дебиторов."""
    if hasattr(app, 'debtors_button_frame'):
        app.debtors_button_frame.destroy()
    button_frame = ttk.Frame(app.debtors_table_frame)
    button_frame.grid(row=len(app.debtors_rows) + 1, column=0, sticky="ew", pady=5)
    button_frame.grid_columnconfigure((0, 1, 2), weight=1)
    app.debtors_button_frame = button_frame
    ttk.Button(button_frame, text="+ Добавить строку",
               command=lambda: add_debtors_row(app)).grid(row=0, column=0, sticky="ew", padx=5)
    ttk.Button(button_frame, text="Анализ",
               command=lambda: analyze_debtors(app)).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(button_frame, text="Настроить заказчиков",
               command=lambda: app.open_settings("customers")).grid(row=0, column=2, sticky="ew", padx=5)

def add_creditors_row(app: Any) -> None:
    """Добавляет строку для кредиторов."""
    if len(app.creditors_rows) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        return
    columns = [
        {"type": "combobox", "values_key": "suppliers"},
        {"type": "entry"}
    ]
    row_idx = len(app.creditors_rows) + 1  # Индекс строки начинается с 1 (после заголовков)
    row = create_row(
        app.creditors_table_frame,
        columns,
        lambda r: add_creditor_row(app, r),
        lambda r: delete_creditor_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.creditors_rows.append(row)
    app.creditors_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()

def add_debtors_row(app: Any) -> None:
    """Добавляет строку для дебиторов."""
    if len(app.debtors_rows) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        return
    columns = [
        {"type": "combobox", "values_key": "customers"},
        {"type": "entry"}
    ]
    row_idx = len(app.debtors_rows) + 1  # Индекс строки начинается с 1 (после заголовков)
    row = create_row(
        app.debtors_table_frame,
        columns,
        lambda r: add_debtor_row(app, r),
        lambda r: delete_debtor_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.debtors_rows.append(row)
    app.debtors_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()

def add_creditor_row(app: Any, row: List[Any]) -> None:
    """Добавляет данные о кредиторе."""
    try:
        supplier = row[0].get()
        if not supplier:
            messagebox.showerror("Ошибка", "Выберите или введите поставщика.")
            return
        amount = locale.atof(row[1].get() or '0')
        current_date = datetime.now().strftime("%Y-%m-%d")  # Добавляем текущую дату
        app.state.current_snapshot.balance.liabilities["creditors"].append((supplier, amount, current_date))
        for state in app.creditors_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        if supplier not in app.state.settings["suppliers"]:
            app.state.settings["suppliers"].append(supplier)
            app.save_settings()
            for r in app.creditors_rows:
                r[0]["values"] = app.state.settings["suppliers"]
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен кредитор: {supplier}")
    except ValueError as e:
        log_message(f"Ошибка при добавлении кредитора: {e}", level="ERROR")
        messagebox.showerror("Ошибка", "Введите числовое значение.")
        update_status(app, "Ошибка: некорректное числовое значение")

def add_debtor_row(app: Any, row: List[Any]) -> None:
    """Добавляет данные о дебиторе."""
    try:
        customer = row[0].get()
        if not customer:
            messagebox.showerror("Ошибка", "Выберите или введите заказчика.")
            return
        amount = locale.atof(row[1].get() or '0')
        current_date = datetime.now().strftime("%Y-%m-%d")  # Добавляем текущую дату
        app.state.current_snapshot.balance.assets["debtors"].append((customer, amount, current_date))
        for state in app.debtors_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        if customer not in app.state.settings["customers"]:
            app.state.settings["customers"].append(customer)
            app.save_settings()
            for r in app.debtors_rows:
                r[0]["values"] = app.state.settings["customers"]
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен дебитор: {customer}")
    except ValueError as e:
        log_message(f"Ошибка при добавлении дебитора: {e}", level="ERROR")
        messagebox.showerror("Ошибка", "Введите числовое значение.")
        update_status(app, "Ошибка: некорректное числовое значение")

def delete_creditor_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку кредитора."""
    supplier = row[0].get()
    app.state.current_snapshot.balance.liabilities["creditors"] = [
        c for c in app.state.current_snapshot.balance.liabilities["creditors"] if c[0] != supplier
    ]
    index = app.creditors_rows.index(row)
    app.creditors_rows.pop(index)
    app.creditors_rows_state.pop(index)
    for widget in app.creditors_table_frame.winfo_children():
        widget.destroy()

    app.creditors_rows.clear()
    app.creditors_rows_state.clear()
    app.creditors_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Поставщик", "Сумма (факт), ₽"]
    header_frame = ttk.Frame(app.creditors_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(len(app.creditors_rows_state)):
        app.creditors_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_creditors_row(app)

    app.update_dashboard()
    app.update_tab_indicators()
    _create_creditors_buttons(app)
    update_status(app, f"Удалён кредитор: {supplier}")

def delete_debtor_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку дебитора."""
    customer = row[0].get()
    app.state.current_snapshot.balance.assets["debtors"] = [
        d for d in app.state.current_snapshot.balance.assets["debtors"] if d[0] != customer
    ]
    index = app.debtors_rows.index(row)
    app.debtors_rows.pop(index)
    app.debtors_rows_state.pop(index)
    for widget in app.debtors_table_frame.winfo_children():
        widget.destroy()

    app.debtors_rows.clear()
    app.debtors_rows_state.clear()
    app.debtors_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Заказчик", "Сумма (факт), ₽"]
    header_frame = ttk.Frame(app.debtors_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx in range(len(app.debtors_rows_state)):
        app.debtors_table_frame.grid_rowconfigure(idx + 1, weight=0)
        add_debtors_row(app)

    app.update_dashboard()
    app.update_tab_indicators()
    _create_debtors_buttons(app)
    update_status(app, f"Удалён дебитор: {customer}")

def analyze_creditors(app: Any) -> None:
    """Запускает анализ кредиторов через Owl."""
    try:
        app.owl_respond_command("проверь кредиторов")
        update_status(app, "Запущен анализ кредиторов")
    except Exception as e:
        log_message(f"Ошибка при запуске анализа кредиторов: {e}", level="ERROR")
        update_status(app, f"Ошибка анализа кредиторов: {e}")

def analyze_debtors(app: Any) -> None:
    """Запускает анализ дебиторов через Owl."""
    try:
        app.owl_respond_command("проверь дебиторов")
        update_status(app, "Запущен анализ дебиторов")
    except Exception as e:
        log_message(f"Ошибка при запуске анализа дебиторов: {e}", level="ERROR")
        update_status(app, f"Ошибка анализа дебиторов: {e}")