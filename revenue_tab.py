import tkinter as tk
from tkinter import ttk, messagebox
import locale
from datetime import datetime
from components import create_row
from utils import update_status, log_message
from typing import Any, List
from data_processing import filter_by_period

def build_revenue(app: Any) -> None:
    """Creates the Revenue tab for revenue accounting."""
    locale.setlocale(locale.LC_ALL, '')
    revenue_frame = ttk.Frame(app.tab_revenue, padding=15)
    revenue_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    entity_frame = ttk.Frame(revenue_frame)
    entity_frame.pack(fill="x", pady=5)
    entity_frame.grid_columnconfigure((0, 1, 2), weight=1)
    ttk.Label(entity_frame, text="Юрлицо:").grid(row=0, column=0, sticky="w")
    app.entity_type = tk.StringVar(value="ООО")
    ttk.Radiobutton(entity_frame, text="ООО", value="ООО", variable=app.entity_type,
                    command=lambda: switch_entity(app)).grid(row=0, column=1, padx=5, sticky="w")
    ttk.Radiobutton(entity_frame, text="ИП", value="ИП", variable=app.entity_type,
                    command=lambda: switch_entity(app)).grid(row=0, column=2, padx=5, sticky="w")

    app.revenue_table_frame = ttk.LabelFrame(revenue_frame, text="Данные выручки", padding=10)
    app.revenue_table_frame.pack(fill="both", expand=True)

    app.revenue_rows = []
    app.revenue_rows_state = []

    app.revenue_table_frame.grid_columnconfigure(0, weight=1)
    headers = ["Заказчик", "Оборот (факт), ₽", "Койко-дни (факт)", "Стоимость/день, ₽", "Себестоимость, ₽"]
    header_frame = ttk.Frame(app.revenue_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1, uniform="rev")
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    filtered_revenue = filter_by_period([r.__dict__ for r in app.state.current_snapshot.revenue], period_dict)
    existing_customers = {row["customer"] for row in filtered_revenue}

    row_idx = 1
    for revenue_row in filtered_revenue:
        row = create_row(
            app.revenue_table_frame,
            [
                {"type": "combobox", "values_key": "customers"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"}
            ],
            lambda r: add_revenue_data_row(app, r),
            lambda r: delete_revenue_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        row[0].set(revenue_row["customer"])
        row[1].insert(0, str(revenue_row["turnover_fact"]))
        row[2].insert(0, str(revenue_row["beds_fact"]))
        row[3].insert(0, str(revenue_row["cost"]))
        row[4].insert(0, str(revenue_row["sebestoimost"]))
        row[-1].config(background="green")
        app.revenue_rows.append(row)
        app.revenue_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
        row_idx += 1

    for _ in range(5 - len(filtered_revenue)):
        app.revenue_table_frame.grid_rowconfigure(row_idx, weight=0)
        add_revenue_row(app)
        row_idx += 1

    _create_revenue_buttons(app)

def _create_revenue_buttons(app: Any) -> None:
    """Creates control buttons for the revenue tab."""
    if hasattr(app, 'revenue_button_frame'):
        app.revenue_button_frame.destroy()
    app.revenue_button_frame = ttk.Frame(app.revenue_table_frame)
    app.revenue_button_frame.grid(row=len(app.revenue_rows) + 1, column=0, sticky="ew", pady=5)
    app.revenue_button_frame.grid_columnconfigure((0, 1, 2), weight=1)
    ttk.Button(app.revenue_button_frame, text="+ Добавить строку",
               command=lambda: add_revenue_row(app)).grid(row=0, column=0, sticky="ew", padx=5)
    ttk.Button(app.revenue_button_frame, text="Анализ",
               command=lambda: analyze_revenue(app)).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(app.revenue_button_frame, text="Настроить заказчиков",
               command=lambda: app.open_settings("customers")).grid(row=0, column=2, sticky="ew", padx=5)

def switch_entity(app: Any) -> None:
    """Switches the interface based on the legal entity type."""
    entity = app.entity_type.get()
    headers = ["Заказчик", "Оборот (факт), ₽", "Койко-дни (факт)", "Стоимость/день, ₽", "Себестоимость, ₽"] if entity == "ООО" else ["Буфет", "Оборот (факт), ₽", "Наличные, ₽", "Безналичные, ₽"]
    for widget in app.revenue_table_frame.winfo_children():
        widget.destroy()

    app.revenue_rows.clear()
    app.revenue_rows_state.clear()

    app.revenue_table_frame.grid_columnconfigure(0, weight=1)
    header_frame = ttk.Frame(app.revenue_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1, uniform="rev")
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    filtered_revenue = filter_by_period([r.__dict__ for r in app.state.current_snapshot.revenue if r["legal_entity"] == entity], period_dict)
    existing_customers = {row["customer"] for row in filtered_revenue}

    row_idx = 1
    for revenue_row in filtered_revenue:
        columns = [
            {"type": "combobox", "values_key": "customers"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"}
        ] if entity == "ООО" else [
            {"type": "combobox", "values_key": "customers"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"}
        ]
        row = create_row(
            app.revenue_table_frame,
            columns,
            lambda r: add_revenue_data_row(app, r),
            lambda r: delete_revenue_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        row[0].set(revenue_row["customer"])
        row[1].insert(0, str(revenue_row["turnover_fact"]))
        if entity == "ООО":
            row[2].insert(0, str(revenue_row["beds_fact"]))
            row[3].insert(0, str(revenue_row["cost"]))
            row[4].insert(0, str(revenue_row["sebestoimost"]))
        else:
            row[2].insert(0, str(revenue_row["cash_part"]))
            row[3].insert(0, str(revenue_row["noncash_part"]))
        row[-1].config(background="green")
        app.revenue_rows.append(row)
        app.revenue_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})
        row_idx += 1

    for _ in range(5 - len(filtered_revenue)):
        app.revenue_table_frame.grid_rowconfigure(row_idx, weight=0)
        add_revenue_row(app)
        row_idx += 1

    _create_revenue_buttons(app)

def add_revenue_row(app: Any) -> None:
    """Adds a row for entering revenue data."""
    entity = app.entity_type.get()
    if entity == "ООО":
        columns = [
            {"type": "combobox", "values_key": "customers"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"}
        ]
    else:
        columns = [
            {"type": "combobox", "values_key": "customers"},
            {"type": "entry"},
            {"type": "entry"},
            {"type": "entry"}
        ]

    row_idx = len(app.revenue_rows) + 1
    row = create_row(
        app.revenue_table_frame,
        columns,
        lambda r: add_revenue_data_row(app, r),
        lambda r: delete_revenue_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.revenue_rows.append(row)
    app.revenue_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    _create_revenue_buttons(app)

def add_revenue_data_row(app: Any, row: List[Any]) -> None:
    """Adds revenue data."""
    try:
        customer = row[0].get()
        if not customer:
            messagebox.showerror("Ошибка", "Выберите или введите заказчика/буфет.")
            return
        entity = app.entity_type.get()
        turnover_fact = locale.atof(row[1].get() or '0')
        current_date = datetime.now().strftime("%Y-%m-%d")

        if entity == "ООО":
            beds_fact = locale.atof(row[2].get() or '0')
            cost = locale.atof(row[3].get() or '0')
            sebestoimost = locale.atof(row[4].get() or '0')
            revenue_row = app.state.RevenueRow(
                customer=customer,
                legal_entity=entity,
                turnover_fact=turnover_fact,
                beds_fact=beds_fact,
                cost=cost,
                sebestoimost=sebestoimost,
                turnover_plan=0,
                beds_plan=0,
                cash_part=0,
                noncash_part=0,
                date=current_date
            )
        else:
            cash_part = locale.atof(row[2].get() or '0')
            noncash_part = locale.atof(row[3].get() or '0')
            if abs(cash_part + noncash_part - turnover_fact) > 0.01:
                messagebox.showerror("Ошибка", "Сумма наличных и безналичных должна равняться обороту.")
                return
            revenue_row = app.state.RevenueRow(
                customer=customer,
                legal_entity=entity,
                turnover_fact=turnover_fact,
                beds_fact=0,
                cost=0,
                sebestoimost=0,
                turnover_plan=0,
                beds_plan=0,
                cash_part=cash_part,
                noncash_part=noncash_part,
                date=current_date
            )
            # Add cash_part to cash.income for IP (buffets)
            app.state.current_snapshot.cash.income += cash_part
            cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
            app.status_label.config(text=f"Добавлена выручка для {customer}. Наличные поступления: {cash_part:,.0f} руб. Доступно: {cash_available:,.0f} руб")

        app.state.current_snapshot.revenue.append(revenue_row)
        for state in app.revenue_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        if customer not in app.state.settings["customers"]:
            app.state.settings["customers"].append(customer)
            app.save_settings()
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлена выручка для {customer}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовые значения.")
        update_status(app, "Ошибка: некорректные числовые значения")

def delete_revenue_row(app: Any, row: List[Any]) -> None:
    """Deletes a revenue row."""
    customer = row[0].get()
    # Remove cash_part from cash.income if the row is for IP
    for revenue_row in app.state.current_snapshot.revenue:
        if revenue_row.customer == customer and revenue_row.legal_entity == "ИП":
            app.state.current_snapshot.cash.income -= revenue_row.cash_part
            break
    app.state.current_snapshot.revenue = [
        r for r in app.state.current_snapshot.revenue if r.customer != customer
    ]
    index = app.revenue_rows.index(row)
    app.revenue_rows.pop(index)
    app.revenue_rows_state.pop(index)

    for widget in app.revenue_table_frame.winfo_children():
        widget.destroy()

    headers = ["Заказчик", "Оборот (факт), ₽", "Койко-дни (факт)", "Стоимость/день, ₽", "Себестоимость, ₽"] if app.entity_type.get() == "ООО" else ["Буфет", "Оборот (факт), ₽", "Наличные, ₽", "Безналичные, ₽"]
    header_frame = ttk.Frame(app.revenue_table_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=5)
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1, uniform="rev")
        ttk.Label(header_frame, text=header).grid(row=0, column=i, padx=5, sticky="ew")

    for idx, (r, s) in enumerate(zip(app.revenue_rows, app.revenue_rows_state)):
        entity = app.entity_type.get()
        if entity == "ООО":
            columns = [
                {"type": "combobox", "values_key": "customers"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"}
            ]
        else:
            columns = [
                {"type": "combobox", "values_key": "customers"},
                {"type": "entry"},
                {"type": "entry"},
                {"type": "entry"}
            ]
        new_row = create_row(
            app.revenue_table_frame,
            columns,
            lambda r: add_revenue_data_row(app, r),
            lambda r: delete_revenue_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        r[:] = new_row
        s["indicator"] = new_row[-1]
        s["row"] = new_row

    _create_revenue_buttons(app)
    app.update_dashboard()
    app.update_tab_indicators()
    update_status(app, f"Удалена строка: {customer}")

def analyze_revenue(app: Any) -> None:
    """Launches revenue analysis via Owl."""
    app.owl_respond_command("проверь выручку")
    update_status(app, "Запущен анализ выручки")