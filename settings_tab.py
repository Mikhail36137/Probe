import tkinter as tk
from tkinter import ttk, messagebox
from components import create_row
from utils import update_status
from typing import Any, List, Dict
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def build_settings(app: Any) -> None:
    """Создаёт окно настроек."""
    settings_window = tk.Toplevel(app.root)
    settings_window.title("Настройки")
    settings_window.geometry("600x400")

    notebook = ttk.Notebook(settings_window)
    notebook.pack(fill="both", expand=True)

    # Вкладка "Поставщики"
    suppliers_frame = ttk.Frame(notebook, padding=10)
    notebook.add(suppliers_frame, text="Поставщики")

    app.suppliers_inner_frame = ttk.Frame(suppliers_frame)
    app.suppliers_inner_frame.pack(fill="both", expand=True)

    app.suppliers_rows: List[List] = []
    app.suppliers_rows_state: List[Dict] = []

    headers = ["Поставщик", ""]
    header_frame = ttk.Frame(app.suppliers_inner_frame)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    # Инициализация строк поставщиков из настроек
    row_idx = 1
    for supplier in app.state.settings.get("suppliers", []):
        row = create_row(
            app.suppliers_inner_frame,
            [{"type": "entry"}],
            lambda r: add_supplier_row(app, r),
            lambda r: delete_supplier_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        row[0].insert(0, supplier)
        row[-1].config(background="green")
        app.suppliers_rows.append(row)
        app.suppliers_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
        row_idx += 1

    ttk.Button(suppliers_frame, text="Добавить поставщика", command=lambda: add_supplier_row(app)).pack(pady=5)

    # Вкладка "Заказчики"
    customers_frame = ttk.Frame(notebook, padding=10)
    notebook.add(customers_frame, text="Заказчики")

    app.customers_inner_frame = ttk.Frame(customers_frame)
    app.customers_inner_frame.pack(fill="both", expand=True)

    app.customers_rows: List[List] = []
    app.customers_rows_state: List[Dict] = []

    headers = ["Заказчик", ""]
    header_frame = ttk.Frame(app.customers_inner_frame)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    # Инициализация строк заказчиков из настроек
    row_idx = 1
    for customer in app.state.settings.get("customers", []):
        row = create_row(
            app.customers_inner_frame,
            [{"type": "entry"}],
            lambda r: add_customer_row(app, r),
            lambda r: delete_customer_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        row[0].insert(0, customer)
        row[-1].config(background="green")
        app.customers_rows.append(row)
        app.customers_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
        row_idx += 1

    ttk.Button(customers_frame, text="Добавить заказчика", command=lambda: add_customer_row(app)).pack(pady=5)

    # Кнопка сохранения
    ttk.Button(settings_window, text="Сохранить настройки", command=lambda: save_settings(app, settings_window)).pack(pady=10)

def add_supplier_row(app: Any, row: List[Any] = None) -> None:
    """Добавляет строку для поставщика."""
    logging.debug("Добавление нового поставщика")
    row_idx = len(app.suppliers_rows) + 1
    new_row = create_row(
        app.suppliers_inner_frame,
        [{"type": "entry"}],
        lambda r: add_supplier_row(app, r),
        lambda r: delete_supplier_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    if row:  # Если это редактирование существующей строки
        supplier = row[0].get()
        if not supplier:
            messagebox.showerror("Ошибка", "Введите название поставщика.")
            return
        new_row[0].insert(0, supplier)
        # Удаляем старую строку из списка
        index = app.suppliers_rows.index(row)
        app.suppliers_rows.pop(index)
        app.suppliers_rows_state.pop(index)
        logging.debug(f"Отредактирован поставщик: {supplier}")
    app.suppliers_rows.append(new_row)
    app.suppliers_rows_state.append({"indicator": new_row[-1], "added": False, "used_in_calculation": False, "row": new_row})
    app.update_tab_indicators()
    # Обновляем интерфейс
    refresh_suppliers(app)
    logging.debug(f"Добавлена строка поставщика, общее количество строк: {len(app.suppliers_rows)}")

def delete_supplier_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку поставщика."""
    logging.debug("Удаление поставщика")
    index = app.suppliers_rows.index(row)
    supplier = row[0].get()
    app.suppliers_rows.pop(index)
    app.suppliers_rows_state.pop(index)
    refresh_suppliers(app)
    app.update_tab_indicators()
    logging.debug(f"Удалён поставщик: {supplier}")

def add_customer_row(app: Any, row: List[Any] = None) -> None:
    """Добавляет строку для заказчика."""
    logging.debug("Добавление нового заказчика")
    row_idx = len(app.customers_rows) + 1
    new_row = create_row(
        app.customers_inner_frame,
        [{"type": "entry"}],
        lambda r: add_customer_row(app, r),
        lambda r: delete_customer_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    if row:  # Если это редактирование существующей строки
        customer = row[0].get()
        if not customer:
            messagebox.showerror("Ошибка", "Введите название заказчика.")
            return
        new_row[0].insert(0, customer)
        # Удаляем старую строку из списка
        index = app.customers_rows.index(row)
        app.customers_rows.pop(index)
        app.customers_rows_state.pop(index)
        logging.debug(f"Отредактирован заказчик: {customer}")
    app.customers_rows.append(new_row)
    app.customers_rows_state.append({"indicator": new_row[-1], "added": False, "used_in_calculation": False, "row": new_row})
    app.update_tab_indicators()
    # Обновляем интерфейс
    refresh_customers(app)
    logging.debug(f"Добавлена строка заказчика, общее количество строк: {len(app.customers_rows)}")

def delete_customer_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку заказчика."""
    logging.debug("Удаление заказчика")
    index = app.customers_rows.index(row)
    customer = row[0].get()
    app.customers_rows.pop(index)
    app.customers_rows_state.pop(index)
    refresh_customers(app)
    app.update_tab_indicators()
    logging.debug(f"Удалён заказчик: {customer}")

def refresh_suppliers(app: Any) -> None:
    """Обновляет список поставщиков в интерфейсе."""
    logging.debug("Обновление списка поставщиков в интерфейсе")
    for widget in app.suppliers_inner_frame.winfo_children():
        widget.destroy()

    headers = ["Поставщик", ""]
    header_frame = ttk.Frame(app.suppliers_inner_frame)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    row_idx = 1
    new_rows = []
    new_states = []
    for r, s in zip(app.suppliers_rows, app.suppliers_rows_state):
        new_row = create_row(
            app.suppliers_inner_frame,
            [{"type": "entry"}],
            lambda r: add_supplier_row(app, r),
            lambda r: delete_supplier_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        supplier = r[0].get()
        new_row[0].insert(0, supplier)
        new_row[-1].config(background="green" if s["added"] else "red")
        new_rows.append(new_row)
        new_states.append({"indicator": new_row[-1], "added": s["added"], "used_in_calculation": s["used_in_calculation"], "row": new_row})
        row_idx += 1

    app.suppliers_rows = new_rows
    app.suppliers_rows_state = new_states
    logging.debug(f"Обновлено поставщиков: {len(app.suppliers_rows)}")

def refresh_customers(app: Any) -> None:
    """Обновляет список заказчиков в интерфейсе."""
    logging.debug("Обновление списка заказчиков в интерфейсе")
    for widget in app.customers_inner_frame.winfo_children():
        widget.destroy()

    headers = ["Заказчик", ""]
    header_frame = ttk.Frame(app.customers_inner_frame)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    row_idx = 1
    new_rows = []
    new_states = []
    for r, s in zip(app.customers_rows, app.customers_rows_state):
        new_row = create_row(
            app.customers_inner_frame,
            [{"type": "entry"}],
            lambda r: add_customer_row(app, r),
            lambda r: delete_customer_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        customer = r[0].get()
        new_row[0].insert(0, customer)
        new_row[-1].config(background="green" if s["added"] else "red")
        new_rows.append(new_row)
        new_states.append({"indicator": new_row[-1], "added": s["added"], "used_in_calculation": s["used_in_calculation"], "row": new_row})
        row_idx += 1

    app.customers_rows = new_rows
    app.customers_rows_state = new_states
    logging.debug(f"Обновлено заказчиков: {len(app.customers_rows)}")

def save_settings(app: Any, window: tk.Toplevel) -> None:
    """Сохраняет настройки."""
    logging.debug("Сохранение настроек")
    # Собираем списки поставщиков и заказчиков
    suppliers = []
    for row in app.suppliers_rows:
        supplier = row[0].get().strip()
        if supplier and supplier not in suppliers:
            suppliers.append(supplier)

    customers = []
    for row in app.customers_rows:
        customer = row[0].get().strip()
        if customer and customer not in customers:
            customers.append(customer)

    # Обновляем app.state.settings
    app.state.settings["suppliers"] = suppliers
    app.state.settings["customers"] = customers

    # Сохраняем настройки
    app.save_settings()

    # Обновляем Combobox в revenue_tab
    from revenue_tab import build_revenue
    build_revenue(app)

    logging.debug(f"Сохранено поставщиков: {len(suppliers)}, заказчиков: {len(customers)}")
    update_status(app, "Настройки сохранены")
    window.destroy()