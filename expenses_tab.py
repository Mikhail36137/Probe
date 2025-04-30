import tkinter as tk
from tkinter import ttk, messagebox
import locale
from datetime import datetime
from components import create_row
from utils import update_status
from typing import Any, List
from data_processing import filter_by_period

def build_expenses(app: Any) -> None:
    """Creates the Expenses tab for expense accounting."""
    locale.setlocale(locale.LC_ALL, '')
    expenses_frame = ttk.Frame(app.tab_expenses, padding=15)
    expenses_frame.grid(row=0, column=0, sticky="nsew")
    expenses_frame.grid_rowconfigure(0, weight=1)
    expenses_frame.grid_columnconfigure(0, weight=1)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    # Non-cash expenses
    noncash_frame = ttk.LabelFrame(expenses_frame, text="Безналичные расходы", padding=10)
    noncash_frame.grid(row=0, column=0, sticky="nsew", pady=5)
    noncash_frame.grid_rowconfigure(1, weight=1)
    noncash_frame.grid_columnconfigure(0, weight=1)

    app.noncash_rows = []
    app.noncash_rows_state = []

    headers = ["Дата", "Категория", "Контрагент", "Сумма, ₽", "Канал"]
    header_frame = ttk.Frame(noncash_frame)
    header_frame.grid(row=0, column=0, sticky="ew")
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5)

    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    filtered_expenses = filter_by_period([e.__dict__ for e in app.state.current_snapshot.expenses], period_dict)

    row_idx = 1
    for expense in filtered_expenses:
        if expense["channel"] == "noncash":
            row = create_row(
                noncash_frame,
                [
                    {"type": "entry"},
                    {"type": "combobox", "values_key": "expense_categories"},
                    {"type": "entry"},
                    {"type": "entry"},
                    {"type": "entry"}
                ],
                lambda r: add_noncash_row(app, r),
                lambda r: delete_noncash_row(app, r),
                app.state.settings,
                row_idx=row_idx
            )
            row[0].insert(0, expense["date"])
            row[1].set(expense["category"])
            row[2].insert(0, expense["contractor"])
            row[3].insert(0, str(expense["amount"]))
            row[4].insert(0, expense["channel"])
            row[-1].config(background="green")
            app.noncash_rows.append(row)
            app.noncash_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
            row_idx += 1

    for _ in range(5 - len([e for e in filtered_expenses if e["channel"] == "noncash"])):
        row = create_row(
            noncash_frame,
            [
                {"type": "entry"},
                {"type": "combobox", "values_key": "expense_categories"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"}
            ],
            lambda r: add_noncash_row(app, r),
            lambda r: delete_noncash_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        app.noncash_rows.append(row)
        app.noncash_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
        row_idx += 1

    # Cash expenses
    cash_frame = ttk.LabelFrame(expenses_frame, text="Наличные расходы", padding=10)
    cash_frame.grid(row=1, column=0, sticky="nsew", pady=5)
    cash_frame.grid_rowconfigure(0, weight=1)
    cash_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(cash_frame, text="Распределить наличные", command=lambda: distribute_cash(app)).grid(row=0, column=0, pady=5, sticky="w")

    # Cash balance
    cash_balance_frame = ttk.LabelFrame(expenses_frame, text="Баланс наличных", padding=5)
    cash_balance_frame.grid(row=2, column=0, sticky="ew", pady=5)

    ttk.Label(cash_balance_frame, text=f"Начальный остаток: {app.state.current_snapshot.cash.start:,.0f} руб").grid(row=0, column=0, sticky="w")
    ttk.Label(cash_balance_frame, text=f"Поступления: {app.state.current_snapshot.cash.income:,.0f} руб").grid(row=1, column=0, sticky="w")
    ttk.Label(cash_balance_frame, text=f"Расходы: {app.state.current_snapshot.cash.expenses:,.0f} руб").grid(row=2, column=0, sticky="w")
    ttk.Label(cash_balance_frame, text=f"Конечный остаток: {app.state.current_snapshot.cash.end:,.0f} руб").grid(row=3, column=0, sticky="w")
    cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
    app.cash_available_label = ttk.Label(cash_balance_frame, text=f"Доступно для распределения: {cash_available:,.0f} руб")
    app.cash_available_label.grid(row=4, column=0, sticky="w")

def add_noncash_row(app: Any, row: List[Any]) -> None:
    """Adds a non-cash expense row."""
    try:
        date = row[0].get()
        category = row[1].get()
        contractor = row[2].get()
        amount = locale.atof(row[3].get() or '0')
        channel = row[4].get()

        if not date or not category or not amount:
            messagebox.showerror("Ошибка", "Заполните дату, категорию и сумму.")
            return

        expense_row = app.state.ExpenseRow(
            date=date,
            category=category,
            contractor=contractor,
            amount=amount,
            channel=channel,
            plan=0
        )

        app.state.current_snapshot.expenses.append(expense_row)
        for state in app.noncash_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен безналичный расход: {category}, {amount:,.0f} руб")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректные числовые значения.")
        update_status(app, "Ошибка: некорректные числовые значения")

def delete_noncash_row(app: Any, row: List[Any]) -> None:
    """Deletes a non-cash expense row."""
    date = row[0].get()
    category = row[1].get()
    contractor = row[2].get()
    amount = locale.atof(row[3].get() or '0')
    channel = row[4].get()

    app.state.current_snapshot.expenses = [
        e for e in app.state.current_snapshot.expenses
        if not (e.date == date and e.category == category and e.contractor == contractor and e.amount == amount and e.channel == channel)
    ]
    index = app.noncash_rows.index(row)
    app.noncash_rows.pop(index)
    app.noncash_rows_state.pop(index)

    for widget in row[0].master.winfo_children():
        widget.destroy()

    headers = ["Дата", "Категория", "Контрагент", "Сумма, ₽", "Канал"]
    header_frame = ttk.Frame(row[0].master)
    header_frame.grid(row=0, column=0, sticky="ew")
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1)
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5)

    for idx, (r, s) in enumerate(zip(app.noncash_rows, app.noncash_rows_state)):
        new_row = create_row(
            row[0].master,
            [
                {"type": "entry"},
                {"type": "combobox", "values_key": "expense_categories"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"}
            ],
            lambda r: add_noncash_row(app, r),
            lambda r: delete_noncash_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        r[:] = new_row
        s["indicator"] = new_row[-1]
        s["row"] = new_row

    app.update_dashboard()
    app.update_tab_indicators()
    update_status(app, f"Удален безналичный расход: {category}")

def distribute_cash(app: Any) -> None:
    """Opens a window to distribute cash expenses."""
    cash_window = tk.Toplevel(app.root)
    cash_window.title("Распределение наличных расходов")
    cash_window.geometry("600x400")

    cash_frame = ttk.Frame(cash_window, padding=10)
    cash_frame.pack(fill="both", expand=True)

    # Display available cash
    cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
    remaining_label = ttk.Label(cash_frame, text=f"Доступно для распределения: {cash_available:,.0f} руб")
    remaining_label.pack(anchor="w", pady=5)

    app.cash_rows = []
    app.cash_rows_state = []

    headers = ["Дата", "Категория", "Контрагент", "Сумма, ₽"]
    header_frame = ttk.Frame(cash_frame)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    row_idx = 1
    for expense in app.state.current_snapshot.expenses:
        if expense.channel == "cash":
            row = create_row(
                cash_frame,
                [
                    {"type": "entry"},
                    {"type": "combobox", "values_key": "expense_categories"},
                    {"type": "entry"},
                    {"type": "entry"}
                ],
                lambda r: add_cash_row(app, r, remaining_label),
                lambda r: delete_cash_row(app, r, remaining_label),
                app.state.settings,
                row_idx=row_idx
            )
            row[0].insert(0, expense.date)
            row[1].set(expense.category)
            row[2].insert(0, expense.contractor)
            row[3].insert(0, str(expense.amount))
            row[-1].config(background="green")
            app.cash_rows.append(row)
            app.cash_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
            row_idx += 1

    for _ in range(5 - len([e for e in app.state.current_snapshot.expenses if e.channel == "cash"])):
        row = create_row(
            cash_frame,
            [
                {"type": "entry"},
                {"type": "combobox", "values_key": "expense_categories"},
                {"type": "entry"},
                {"type": "entry"}
            ],
            lambda r: add_cash_row(app, r, remaining_label),
            lambda r: delete_cash_row(app, r, remaining_label),
            app.state.settings,
            row_idx=row_idx
        )
        app.cash_rows.append(row)
        app.cash_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
        row_idx += 1

    ttk.Button(cash_frame, text="Сохранить и закрыть", command=cash_window.destroy).pack(pady=5)

def add_cash_row(app: Any, row: List[Any], remaining_label: ttk.Label) -> None:
    """Adds a cash expense row."""
    try:
        date = row[0].get()
        category = row[1].get()
        contractor = row[2].get()
        amount = locale.atof(row[3].get() or '0')

        if not date or not category or not amount:
            messagebox.showerror("Ошибка", "Заполните дату, категорию и сумму.")
            return

        cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
        if amount > cash_available:
            messagebox.showerror("Ошибка", f"Сумма ({amount:,.0f} руб) превышает доступные наличные ({cash_available:,.0f} руб).")
            return

        expense_row = app.state.ExpenseRow(
            date=date,
            category=category,
            contractor=contractor,
            amount=amount,
            channel="cash",
            plan=0
        )

        app.state.current_snapshot.expenses.append(expense_row)
        app.state.current_snapshot.cash.expenses += amount
        app.state.current_snapshot.cash.end = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses

        for state in app.cash_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")

        cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
        remaining_label.config(text=f"Доступно для распределения: {cash_available:,.0f} руб")
        app.cash_available_label.config(text=f"Доступно для распределения: {cash_available:,.0f} руб")

        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен наличный расход: {category}, {amount:,.0f} руб")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректные числовые значения.")
        update_status(app, "Ошибка: некорректные числовые значения")

def delete_cash_row(app: Any, row: List[Any], remaining_label: ttk.Label) -> None:
    """Deletes a cash expense row."""
    date = row[0].get()
    category = row[1].get()
    contractor = row[2].get()
    amount = locale.atof(row[3].get() or '0')

    app.state.current_snapshot.expenses = [
        e for e in app.state.current_snapshot.expenses
        if not (e.date == date and e.category == category and e.contractor == contractor and e.amount == amount and e.channel == "cash")
    ]
    app.state.current_snapshot.cash.expenses -= amount
    app.state.current_snapshot.cash.end = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses

    index = app.cash_rows.index(row)
    app.cash_rows.pop(index)
    app.cash_rows_state.pop(index)

    for widget in row[0].master.winfo_children():
        widget.destroy()

    headers = ["Дата", "Категория", "Контрагент", "Сумма, ₽"]
    header_frame = ttk.Frame(row[0].master)
    header_frame.pack(fill="x")
    for i, header in enumerate(headers):
        ttk.Label(header_frame, text=header).pack(side="left", padx=5)

    for idx, (r, s) in enumerate(zip(app.cash_rows, app.cash_rows_state)):
        new_row = create_row(
            row[0].master,
            [
                {"type": "entry"},
                {"type": "combobox", "values_key": "expense_categories"},
                {"type": "entry"},
                {"type": "entry"}
            ],
            lambda r: add_cash_row(app, r, remaining_label),
            lambda r: delete_cash_row(app, r, remaining_label),
            app.state.settings,
            row_idx=idx + 1
        )
        r[:] = new_row
        s["indicator"] = new_row[-1]
        s["row"] = new_row

    cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
    remaining_label.config(text=f"Доступно для распределения: {cash_available:,.0f} руб")
    app.cash_available_label.config(text=f"Доступно для распределения: {cash_available:,.0f} руб")

    app.update_dashboard()
    app.update_tab_indicators()
    update_status(app, f"Удален наличный расход: {category}")

def update_noncash_rows(app: Any) -> None:
    """Updates non-cash expense rows after loading a statement."""
    for widget in app.tab_expenses.winfo_children():
        widget.destroy()
    build_expenses(app)