import tkinter as tk
from tkinter import ttk, messagebox
import locale
from datetime import datetime, timedelta
from components import create_row
from utils import update_status, log_message
from typing import Any, List, Dict
from data_processing import load_snapshot, filter_by_period
import matplotlib.pyplot as plt

def build_capital(app: Any) -> None:
    """Creates the Capital tab for managing assets and liabilities."""
    locale.setlocale(locale.LC_ALL, '')
    capital_frame = ttk.Frame(app.tab_capital, padding=15)
    capital_frame.pack(fill="both", expand=True)

    # Настройка стилей для единообразного фона
    style = ttk.Style()
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    # Capitalization overview
    overview_frame = ttk.LabelFrame(capital_frame, text="Обзор капитализации", padding=10)
    overview_frame.pack(fill="x", pady=5)

    # Calculate current capitalization
    total_assets = calculate_total_assets(app.state.current_snapshot)
    total_liabilities = calculate_total_liabilities(app.state.current_snapshot)
    capital = total_assets - total_liabilities

    # Calculate profit for comparison
    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    filtered_revenue = filter_by_period([r.__dict__ for r in app.state.current_snapshot.revenue], period_dict)
    filtered_expenses = filter_by_period([e.__dict__ for e in app.state.current_snapshot.expenses], period_dict)
    total_revenue = sum(row["turnover_fact"] for row in filtered_revenue)
    total_expenses = sum(item["amount"] for item in filtered_expenses)
    profit = total_revenue - total_expenses

    # Calculate delta_cap
    delta_cap = None
    prev_period_key = None
    try:
        end_date = datetime.strptime(period_dict["end_date"], "%Y-%m-%d")
        prev_end_date = (end_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
        prev_start_date = prev_end_date[:8] + "01"
        prev_period_key = f"{prev_start_date}_{prev_end_date}"
        prev_snapshot = load_snapshot(prev_period_key)
        prev_total_assets = calculate_total_assets(prev_snapshot)
        prev_total_liabilities = calculate_total_liabilities(prev_snapshot)
        prev_capital = prev_total_assets - prev_total_liabilities
        delta_cap = capital - prev_capital
    except Exception as e:
        log_message(f"Ошибка при загрузке предыдущего периода: {e}", level="ERROR")
        delta_cap = None

    ttk.Label(overview_frame, text=f"Активы: {total_assets:,.0f} руб").pack(anchor="w")
    ttk.Label(overview_frame, text=f"Пассивы: {total_liabilities:,.0f} руб").pack(anchor="w")
    ttk.Label(overview_frame, text=f"Капитализация: {capital:,.0f} руб").pack(anchor="w")
    ttk.Label(overview_frame, text=f"Δ капитализации: {delta_cap:,.0f} руб" if delta_cap is not None else "Δ капитализации: -").pack(anchor="w")

    if delta_cap is not None and abs(delta_cap - profit) > 0.01:
        ttk.Label(overview_frame, text=f"Внимание: Δ капитализации ({delta_cap:,.0f} руб) не соответствует прибыли ({profit:,.0f} руб)", foreground="red").pack(anchor="w")
    elif delta_cap is not None:
        ttk.Label(overview_frame, text="Δ капитализации соответствует прибыли", foreground="green").pack(anchor="w")

    if delta_cap is not None:
        ttk.Button(overview_frame, text="Показать график сравнения", command=lambda: show_capital_profit_graph(app, capital, delta_cap, profit)).pack(anchor="w", pady=5)

    app.capital_status_label = ttk.Label(capital_frame, text="")
    app.capital_status_label.pack(side="bottom", pady=5)

    assets_frame = ttk.LabelFrame(capital_frame, text="Активы", padding=10)
    assets_frame.pack(fill="both", expand=True)

    app.assets_rows: List[List] = []
    app.assets_rows_state: List[Dict] = []

    # Банковские счета
    bank_accounts_frame = ttk.LabelFrame(assets_frame, text="Банковские счета", padding=5)
    bank_accounts_frame.pack(fill="x", pady=5)

    bank_headers = ["Наименование", "Факт, ₽"]
    bank_header_frame = ttk.Frame(bank_accounts_frame)
    bank_header_frame.pack(fill="x")
    for i, header in enumerate(bank_headers):
        ttk.Label(bank_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    app.bank_account_entries = {}
    for idx, (account, data) in enumerate(app.state.current_snapshot.balance.assets.bank_accounts.items()):
        row_frame = ttk.Frame(bank_accounts_frame)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=account).grid(row=0, column=0, padx=5, sticky="w")
        entry = ttk.Entry(row_frame, width=20, state="normal")
        entry.grid(row=0, column=1, padx=5, sticky="w")
        entry.insert(0, str(data["fact"]))
        app.bank_account_entries[account] = entry

    # Денежные средства (наличные)
    cash_frame = ttk.LabelFrame(assets_frame, text="Денежные средства (наличные)", padding=5)
    cash_frame.pack(fill="x", pady=5)
    ttk.Label(cash_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.cash_entry = ttk.Entry(cash_frame, width=20, state="normal")
    app.cash_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.cash_entry.insert(0, str(app.state.current_snapshot.cash.end))

    # Дебиторская задолженность
    debtors_frame = ttk.LabelFrame(assets_frame, text="Дебиторская задолженность", padding=5)
    debtors_frame.pack(fill="x", pady=5)
    app.debtors_inner_frame = ttk.Frame(debtors_frame)
    app.debtors_inner_frame.pack(fill="both", expand=True)

    debtors_headers = ["Контрагент", "Сумма, ₽"]
    debtors_header_frame = ttk.Frame(app.debtors_inner_frame)
    debtors_header_frame.pack(fill="x")
    for i, header in enumerate(debtors_headers):
        ttk.Label(debtors_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    for idx, debtor in enumerate(app.state.current_snapshot.balance.assets.debtors):
        row = create_row(
            app.debtors_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_debtor_row(app, r),
            lambda r: delete_debtor_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        row[0].insert(0, debtor[0])  # Контрагент
        row[1].insert(0, str(debtor[1]))  # Сумма
        app.assets_rows.append(row)
        app.assets_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})

    # Оборудование
    equipment_frame = ttk.LabelFrame(assets_frame, text="Оборудование", padding=5)
    equipment_frame.pack(fill="x", pady=5)
    app.equipment_inner_frame = ttk.Frame(equipment_frame)
    app.equipment_inner_frame.pack(fill="both", expand=True)

    equipment_headers = ["Наименование", "Количество", "Дата покупки", "Срок службы, лет", "Сумма, ₽"]
    equipment_header_frame = ttk.Frame(app.equipment_inner_frame)
    equipment_header_frame.pack(fill="x")
    for i, header in enumerate(equipment_headers):
        ttk.Label(equipment_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    for idx, equipment in enumerate(app.state.current_snapshot.balance.assets.equipment):
        row = create_row(
            app.equipment_inner_frame,
            [{"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}],
            lambda r: add_equipment_row(app, r),
            lambda r: delete_equipment_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        row[0].insert(0, equipment[0])  # Наименование
        row[1].insert(0, str(equipment[1]))  # Количество
        row[2].insert(0, equipment[2])  # Дата покупки
        row[3].insert(0, str(equipment[3]))  # Срок службы
        row[4].insert(0, str(equipment[4]))  # Сумма
        app.assets_rows.append(row)
        app.assets_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})

    # Инвентарь
    inventory_frame = ttk.LabelFrame(assets_frame, text="Инвентарь", padding=5)
    inventory_frame.pack(fill="x", pady=5)
    app.inventory_inner_frame = ttk.Frame(inventory_frame)
    app.inventory_inner_frame.pack(fill="both", expand=True)

    inventory_headers = ["Наименование", "Сумма, ₽"]
    inventory_header_frame = ttk.Frame(app.inventory_inner_frame)
    inventory_header_frame.pack(fill="x")
    for i, header in enumerate(inventory_headers):
        ttk.Label(inventory_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    for idx, inventory in enumerate(app.state.current_snapshot.balance.assets.inventory):
        row = create_row(
            app.inventory_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_inventory_row(app, r),
            lambda r: delete_inventory_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        row[0].insert(0, inventory[0])  # Наименование
        row[1].insert(0, str(inventory[1]))  # Сумма
        app.assets_rows.append(row)
        app.assets_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})

    # Автотранспорт
    vehicle_frame = ttk.LabelFrame(assets_frame, text="Автотранспорт", padding=5)
    vehicle_frame.pack(fill="x", pady=5)
    app.vehicle_inner_frame = ttk.Frame(vehicle_frame)
    app.vehicle_inner_frame.pack(fill="both", expand=True)

    vehicle_headers = ["Наименование", "Сумма, ₽"]
    vehicle_header_frame = ttk.Frame(app.vehicle_inner_frame)
    vehicle_header_frame.pack(fill="x")
    for i, header in enumerate(vehicle_headers):
        ttk.Label(vehicle_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    for idx, vehicle in enumerate(app.state.current_snapshot.balance.assets.vehicle):
        row = create_row(
            app.vehicle_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_vehicle_row(app, r),
            lambda r: delete_vehicle_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        row[0].insert(0, vehicle[0])  # Наименование
        row[1].insert(0, str(vehicle[1]))  # Сумма
        app.assets_rows.append(row)
        app.assets_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})

    # Остатки на складах
    stocks_frame = ttk.LabelFrame(assets_frame, text="Остатки на складах", padding=5)
    stocks_frame.pack(fill="x", pady=5)

    stocks_headers = ["Наименование", "Факт, ₽"]
    stocks_header_frame = ttk.Frame(stocks_frame)
    stocks_header_frame.pack(fill="x")
    for i, header in enumerate(stocks_headers):
        ttk.Label(stocks_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    app.stocks_entries = {}
    for idx, (stock, data) in enumerate(app.state.current_snapshot.balance.assets.stocks.items()):
        row_frame = ttk.Frame(stocks_frame)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=stock).grid(row=0, column=0, padx=5, sticky="w")
        entry = ttk.Entry(row_frame, width=20, state="normal")
        entry.grid(row=0, column=1, padx=5, sticky="w")
        entry.insert(0, str(data["fact"]))
        app.stocks_entries[stock] = entry

    liabilities_frame = ttk.LabelFrame(capital_frame, text="Пассивы", padding=10)
    liabilities_frame.pack(fill="both", expand=True)

    app.liabilities_rows: List[List] = []
    app.liabilities_rows_state: List[Dict] = []

    # Кредиторская задолженность
    creditors_frame = ttk.LabelFrame(liabilities_frame, text="Кредиторская задолженность", padding=5)
    creditors_frame.pack(fill="x", pady=5)
    app.creditors_inner_frame = ttk.Frame(creditors_frame)
    app.creditors_inner_frame.pack(fill="both", expand=True)

    creditors_headers = ["Контрагент", "Сумма, ₽"]
    creditors_header_frame = ttk.Frame(app.creditors_inner_frame)
    creditors_header_frame.pack(fill="x")
    for i, header in enumerate(creditors_headers):
        ttk.Label(creditors_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    for idx, creditor in enumerate(app.state.current_snapshot.balance.liabilities.creditors):
        row = create_row(
            app.creditors_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_creditor_row(app, r),
            lambda r: delete_creditor_row(app, r),
            app.state.settings,
            row_idx=idx + 1
        )
        row[0].insert(0, creditor[0])  # Контрагент
        row[1].insert(0, str(creditor[1]))  # Сумма
        app.liabilities_rows.append(row)
        app.liabilities_rows_state.append({"indicator": row[-1], "added": True, "used_in_calculation": True, "row": row})

    # Зарплата
    salary_frame = ttk.LabelFrame(liabilities_frame, text="Зарплата", padding=5)
    salary_frame.pack(fill="x", pady=5)
    ttk.Label(salary_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.salary_entry = ttk.Entry(salary_frame, width=20, state="normal")
    app.salary_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.salary_entry.insert(0, str(app.state.current_snapshot.balance.liabilities.salary["fact"]))

    # Налоги
    taxes_frame = ttk.LabelFrame(liabilities_frame, text="Налоги", padding=5)
    taxes_frame.pack(fill="x", pady=5)

    taxes_headers = ["Наименование", "Факт, ₽"]
    taxes_header_frame = ttk.Frame(taxes_frame)
    taxes_header_frame.pack(fill="x")
    for i, header in enumerate(taxes_headers):
        ttk.Label(taxes_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    app.taxes_entries = {}
    for idx, (tax, data) in enumerate(app.state.current_snapshot.balance.liabilities.taxes.items()):
        row_frame = ttk.Frame(taxes_frame)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=tax).grid(row=0, column=0, padx=5, sticky="w")
        entry = ttk.Entry(row_frame, width=20, state="normal")
        entry.grid(row=0, column=1, padx=5, sticky="w")
        entry.insert(0, str(data["fact"]))
        app.taxes_entries[tax] = entry

    # Коммунальные услуги
    utilities_frame = ttk.LabelFrame(liabilities_frame, text="Коммунальные услуги", padding=5)
    utilities_frame.pack(fill="x", pady=5)

    utilities_headers = ["Наименование", "Факт, ₽"]
    utilities_header_frame = ttk.Frame(utilities_frame)
    utilities_header_frame.pack(fill="x")
    for i, header in enumerate(utilities_headers):
        ttk.Label(utilities_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    app.utilities_entries = {}
    for idx, (utility, data) in enumerate(app.state.current_snapshot.balance.liabilities.utilities.items()):
        row_frame = ttk.Frame(utilities_frame)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=utility).grid(row=0, column=0, padx=5, sticky="w")
        entry = ttk.Entry(row_frame, width=20, state="normal")
        entry.grid(row=0, column=1, padx=5, sticky="w")
        entry.insert(0, str(data["fact"]))
        app.utilities_entries[utility] = entry

    # Аренда
    rent_frame = ttk.LabelFrame(liabilities_frame, text="Аренда", padding=5)
    rent_frame.pack(fill="x", pady=5)

    rent_headers = ["Наименование", "Факт, ₽"]
    rent_header_frame = ttk.Frame(rent_frame)
    rent_header_frame.pack(fill="x")
    for i, header in enumerate(rent_headers):
        ttk.Label(rent_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")

    app.rent_entries = {}
    for idx, (rent, data) in enumerate(app.state.current_snapshot.balance.liabilities.rent.items()):
        row_frame = ttk.Frame(rent_frame)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=rent).grid(row=0, column=0, padx=5, sticky="w")
        entry = ttk.Entry(row_frame, width=20, state="normal")
        entry.grid(row=0, column=1, padx=5, sticky="w")
        entry.insert(0, str(data["fact"]))
        app.rent_entries[rent] = entry

    # Бухгалтерия
    accounting_frame = ttk.LabelFrame(liabilities_frame, text="Бухгалтерия", padding=5)
    accounting_frame.pack(fill="x", pady=5)
    ttk.Label(accounting_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.accounting_entry = ttk.Entry(accounting_frame, width=20, state="normal")
    app.accounting_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.accounting_entry.insert(0, str(app.state.current_snapshot.balance.liabilities.accounting["fact"]))

    # Прочие подрядчики
    other_contractors_frame = ttk.LabelFrame(liabilities_frame, text="Прочие подрядчики", padding=5)
    other_contractors_frame.pack(fill="x", pady=5)
    ttk.Label(other_contractors_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.other_contractors_entry = ttk.Entry(other_contractors_frame, width=20, state="normal")
    app.other_contractors_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.other_contractors_entry.insert(0, str(app.state.current_snapshot.balance.liabilities.other_contractors["fact"]))

    # Кредитная линия
    credit_line_frame = ttk.LabelFrame(liabilities_frame, text="Кредитная линия", padding=5)
    credit_line_frame.pack(fill="x", pady=5)
    ttk.Label(credit_line_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.credit_line_entry = ttk.Entry(credit_line_frame, width=20, state="normal")
    app.credit_line_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.credit_line_entry.insert(0, str(app.state.current_snapshot.balance.liabilities.credit_line["fact"]))

    # Кредитная карта
    credit_card_frame = ttk.LabelFrame(liabilities_frame, text="Кредитная карта", padding=5)
    credit_card_frame.pack(fill="x", pady=5)
    ttk.Label(credit_card_frame, text="Факт, ₽").grid(row=0, column=0, padx=5, sticky="w")
    app.credit_card_entry = ttk.Entry(credit_card_frame, width=20, state="normal")
    app.credit_card_entry.grid(row=0, column=1, padx=5, sticky="w")
    app.credit_card_entry.insert(0, str(app.state.current_snapshot.balance.liabilities.credit_card["fact"]))

    # Кнопки управления
    buttons_frame = ttk.Frame(capital_frame)
    buttons_frame.pack(fill="x", pady=10)
    buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
    ttk.Button(buttons_frame, text="Добавить дебитора", command=lambda: add_debtor(app)).grid(row=0, column=0, padx=5, sticky="ew")
    ttk.Button(buttons_frame, text="Добавить оборудование", command=lambda: add_equipment(app)).grid(row=0, column=1, padx=5, sticky="ew")
    ttk.Button(buttons_frame, text="Добавить кредитора", command=lambda: add_creditor(app)).grid(row=0, column=2, padx=5, sticky="ew")

def calculate_total_assets(snapshot: Any) -> float:
    """Calculates total assets."""
    total = sum(item["fact"] for item in snapshot.balance.assets.bank_accounts.values()) + \
            snapshot.cash.end + \
            sum(row[1] for row in snapshot.balance.assets.debtors) + \
            sum(row[4] for row in snapshot.balance.assets.equipment) + \
            sum(row[1] for row in snapshot.balance.assets.inventory) + \
            sum(row[1] for row in snapshot.balance.assets.vehicle) + \
            sum(item["fact"] for item in snapshot.balance.assets.stocks.values())
    return total

def calculate_total_liabilities(snapshot: Any) -> float:
    """Calculates total liabilities."""
    total = sum(row[1] for row in snapshot.balance.liabilities.creditors if row[1] > 0) + \
            snapshot.balance.liabilities.salary["fact"] + \
            sum(item["fact"] for item in snapshot.balance.liabilities.taxes.values()) + \
            sum(item["fact"] for item in snapshot.balance.liabilities.utilities.values()) + \
            sum(item["fact"] for item in snapshot.balance.liabilities.rent.values()) + \
            snapshot.balance.liabilities.accounting["fact"] + \
            snapshot.balance.liabilities.other_contractors["fact"] + \
            snapshot.balance.liabilities.credit_line["fact"] + \
            snapshot.balance.liabilities.credit_card["fact"]
    return total

def show_capital_profit_graph(app: Any, capital: float, delta_cap: float, profit: float) -> None:
    """Shows a graph comparing capitalization and profit."""
    fig, ax = plt.subplots()
    labels = ['Капитализация', 'Δ Капитализации', 'Прибыль']
    values = [capital, delta_cap, profit]
    ax.bar(labels, values, color=['#1e88e5', '#43a047', '#e53935'])
    ax.set_title("Сравнение капитализации и прибыли")
    ax.set_ylabel("Сумма, ₽")
    plt.tight_layout()
    plt.show()

def add_debtor(app: Any) -> None:
    """Adds a debtor row."""
    if len(app.state.current_snapshot.balance.assets.debtors) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        app.capital_status_label.config(text="Ошибка: слишком много строк")
        return
    row_idx = len(app.state.current_snapshot.balance.assets.debtors) + 1
    row = create_row(
        app.debtors_inner_frame,
        [{"type": "entry"}, {"type": "entry"}],
        lambda r: add_debtor_row(app, r),
        lambda r: delete_debtor_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.assets_rows.append(row)
    app.assets_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    app.capital_status_label.config(text="Добавлена строка дебиторской задолженности")

def add_debtor_row(app: Any, row: List[Any]) -> None:
    """Adds a debtor entry."""
    try:
        contractor = row[0].get()
        if not contractor:
            messagebox.showerror("Ошибка", "Введите контрагента.")
            app.capital_status_label.config(text="Ошибка: контрагент не указан")
            return
        amount = locale.atof(row[1].get() or '0')
        app.state.current_snapshot.balance.assets.debtors.append([contractor, amount])
        for state in app.assets_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен дебитор: {contractor}")
        app.capital_status_label.config(text=f"Добавлен дебитор: {contractor}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовое значение для суммы.")
        app.capital_status_label.config(text="Ошибка: некорректная сумма")

def delete_debtor_row(app: Any, row: List[Any]) -> None:
    """Deletes a debtor row."""
    contractor = row[0].get()
    app.state.current_snapshot.balance.assets.debtors = [
        d for d in app.state.current_snapshot.balance.assets.debtors if d[0] != contractor
    ]
    index = app.assets_rows.index(row)
    app.assets_rows.pop(index)
    app.assets_rows_state.pop(index)
    for widget in app.debtors_inner_frame.winfo_children():
        widget.destroy()
    debtors_headers = ["Контрагент", "Сумма, ₽"]
    debtors_header_frame = ttk.Frame(app.debtors_inner_frame)
    debtors_header_frame.pack(fill="x")
    for i, header in enumerate(debtors_headers):
        ttk.Label(debtors_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")
    row_idx = 1
    for idx, (debtor, amount) in enumerate(app.state.current_snapshot.balance.assets.debtors):
        new_row = create_row(
            app.debtors_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_debtor_row(app, r),
            lambda r: delete_debtor_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        new_row[0].insert(0, debtor)
        new_row[1].insert(0, str(amount))
        new_row[-1].config(background="green")
        app.assets_rows[idx] = new_row
        app.assets_rows_state[idx] = {"indicator": new_row[-1], "added": True, "used_in_calculation": True, "row": new_row}
        row_idx += 1
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text=f"Удалён дебитор: {contractor}")

def add_equipment(app: Any) -> None:
    """Adds an equipment row."""
    if len(app.state.current_snapshot.balance.assets.equipment) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        app.capital_status_label.config(text="Ошибка: слишком много строк")
        return
    row_idx = len(app.state.current_snapshot.balance.assets.equipment) + 1
    row = create_row(
        app.equipment_inner_frame,
        [{"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}],
        lambda r: add_equipment_row(app, r),
        lambda r: delete_equipment_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.assets_rows.append(row)
    app.assets_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    app.capital_status_label.config(text="Добавлена строка оборудования")

def add_equipment_row(app: Any, row: List[Any]) -> None:
    """Adds an equipment entry."""
    try:
        name = row[0].get()
        if not name:
            messagebox.showerror("Ошибка", "Введите наименование оборудования.")
            app.capital_status_label.config(text="Ошибка: наименование не указано")
            return
        quantity = int(row[1].get() or '0')
        purchase_date = row[2].get() or datetime.now().strftime("%Y-%m-%d")
        lifespan = int(row[3].get() or '0')
        amount = locale.atof(row[4].get() or '0')
        app.state.current_snapshot.balance.assets.equipment.append([name, quantity, purchase_date, lifespan, amount])
        for state in app.assets_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлено оборудование: {name}")
        app.capital_status_label.config(text=f"Добавлено оборудование: {name}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовые значения для количества, срока службы и суммы.")
        app.capital_status_label.config(text="Ошибка: некорректные значения")

def delete_equipment_row(app: Any, row: List[Any]) -> None:
    """Deletes an equipment row."""
    name = row[0].get()
    app.state.current_snapshot.balance.assets.equipment = [
        e for e in app.state.current_snapshot.balance.assets.equipment if e[0] != name
    ]
    index = app.assets_rows.index(row)
    app.assets_rows.pop(index)
    app.assets_rows_state.pop(index)
    for widget in app.equipment_inner_frame.winfo_children():
        widget.destroy()
    equipment_headers = ["Наименование", "Количество", "Дата покупки", "Срок службы, лет", "Сумма, ₽"]
    equipment_header_frame = ttk.Frame(app.equipment_inner_frame)
    equipment_header_frame.pack(fill="x")
    for i, header in enumerate(equipment_headers):
        ttk.Label(equipment_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")
    row_idx = 1
    for idx, (name, quantity, date, lifespan, amount) in enumerate(app.state.current_snapshot.balance.assets.equipment):
        new_row = create_row(
            app.equipment_inner_frame,
            [{"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}, {"type": "entry"}],
            lambda r: add_equipment_row(app, r),
            lambda r: delete_equipment_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        new_row[0].insert(0, name)
        new_row[1].insert(0, str(quantity))
        new_row[2].insert(0, date)
        new_row[3].insert(0, str(lifespan))
        new_row[4].insert(0, str(amount))
        new_row[-1].config(background="green")
        app.assets_rows[idx] = new_row
        app.assets_rows_state[idx] = {"indicator": new_row[-1], "added": True, "used_in_calculation": True, "row": new_row}
        row_idx += 1
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text=f"Удалено оборудование: {name}")

def add_inventory(app: Any) -> None:
    """Adds an inventory row."""
    if len(app.state.current_snapshot.balance.assets.inventory) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        app.capital_status_label.config(text="Ошибка: слишком много строк")
        return
    row_idx = len(app.state.current_snapshot.balance.assets.inventory) + 1
    row = create_row(
        app.inventory_inner_frame,
        [{"type": "entry"}, {"type": "entry"}],
        lambda r: add_inventory_row(app, r),
        lambda r: delete_inventory_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.assets_rows.append(row)
    app.assets_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    app.capital_status_label.config(text="Добавлена строка инвентаря")

def add_inventory_row(app: Any, row: List[Any]) -> None:
    """Adds an inventory entry."""
    try:
        name = row[0].get()
        if not name:
            messagebox.showerror("Ошибка", "Введите наименование.")
            app.capital_status_label.config(text="Ошибка: наименование не указано")
            return
        amount = locale.atof(row[1].get() or '0')
        app.state.current_snapshot.balance.assets.inventory.append([name, amount])
        for state in app.assets_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен элемент инвентаря: {name}")
        app.capital_status_label.config(text=f"Добавлен элемент инвентаря: {name}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовое значение для суммы.")
        app.capital_status_label.config(text="Ошибка: некорректная сумма")

def delete_inventory_row(app: Any, row: List[Any]) -> None:
    """Deletes an inventory row."""
    name = row[0].get()
    app.state.current_snapshot.balance.assets.inventory = [
        i for i in app.state.current_snapshot.balance.assets.inventory if i[0] != name
    ]
    index = app.assets_rows.index(row)
    app.assets_rows.pop(index)
    app.assets_rows_state.pop(index)
    for widget in app.inventory_inner_frame.winfo_children():
        widget.destroy()
    inventory_headers = ["Наименование", "Сумма, ₽"]
    inventory_header_frame = ttk.Frame(app.inventory_inner_frame)
    inventory_header_frame.pack(fill="x")
    for i, header in enumerate(inventory_headers):
        ttk.Label(inventory_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")
    row_idx = 1
    for idx, (name, amount) in enumerate(app.state.current_snapshot.balance.assets.inventory):
        new_row = create_row(
            app.inventory_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_inventory_row(app, r),
            lambda r: delete_inventory_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        new_row[0].insert(0, name)
        new_row[1].insert(0, str(amount))
        new_row[-1].config(background="green")
        app.assets_rows[idx] = new_row
        app.assets_rows_state[idx] = {"indicator": new_row[-1], "added": True, "used_in_calculation": True, "row": new_row}
        row_idx += 1
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text=f"Удалён элемент инвентаря: {name}")

def add_vehicle(app: Any) -> None:
    """Adds a vehicle row."""
    if len(app.state.current_snapshot.balance.assets.vehicle) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        app.capital_status_label.config(text="Ошибка: слишком много строк")
        return
    row_idx = len(app.state.current_snapshot.balance.assets.vehicle) + 1
    row = create_row(
        app.vehicle_inner_frame,
        [{"type": "entry"}, {"type": "entry"}],
        lambda r: add_vehicle_row(app, r),
        lambda r: delete_vehicle_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.assets_rows.append(row)
    app.assets_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    app.capital_status_label.config(text="Добавлена строка автотранспорта")

def add_vehicle_row(app: Any, row: List[Any]) -> None:
    """Adds a vehicle entry."""
    try:
        name = row[0].get()
        if not name:
            messagebox.showerror("Ошибка", "Введите наименование.")
            app.capital_status_label.config(text="Ошибка: наименование не указано")
            return
        amount = locale.atof(row[1].get() or '0')
        app.state.current_snapshot.balance.assets.vehicle.append([name, amount])
        for state in app.assets_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен автотранспорт: {name}")
        app.capital_status_label.config(text=f"Добавлен автотранспорт: {name}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовое значение для суммы.")
        app.capital_status_label.config(text="Ошибка: некорректная сумма")

def delete_vehicle_row(app: Any, row: List[Any]) -> None:
    """Deletes a vehicle row."""
    name = row[0].get()
    app.state.current_snapshot.balance.assets.vehicle = [
        v for v in app.state.current_snapshot.balance.assets.vehicle if v[0] != name
    ]
    index = app.assets_rows.index(row)
    app.assets_rows.pop(index)
    app.assets_rows_state.pop(index)
    for widget in app.vehicle_inner_frame.winfo_children():
        widget.destroy()
    vehicle_headers = ["Наименование", "Сумма, ₽"]
    vehicle_header_frame = ttk.Frame(app.vehicle_inner_frame)
    vehicle_header_frame.pack(fill="x")
    for i, header in enumerate(vehicle_headers):
        ttk.Label(vehicle_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")
    row_idx = 1
    for idx, (name, amount) in enumerate(app.state.current_snapshot.balance.assets.vehicle):
        new_row = create_row(
            app.vehicle_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_vehicle_row(app, r),
            lambda r: delete_vehicle_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        new_row[0].insert(0, name)
        new_row[1].insert(0, str(amount))
        new_row[-1].config(background="green")
        app.assets_rows[idx] = new_row
        app.assets_rows_state[idx] = {"indicator": new_row[-1], "added": True, "used_in_calculation": True, "row": new_row}
        row_idx += 1
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text=f"Удалён автотранспорт: {name}")

def add_creditor(app: Any) -> None:
    """Adds a creditor row."""
    if len(app.state.current_snapshot.balance.liabilities.creditors) >= 20:
        messagebox.showwarning("Предупреждение", "Достигнуто максимальное количество строк (20).")
        app.capital_status_label.config(text="Ошибка: слишком много строк")
        return
    row_idx = len(app.state.current_snapshot.balance.liabilities.creditors) + 1
    row = create_row(
        app.creditors_inner_frame,
        [{"type": "entry"}, {"type": "entry"}],
        lambda r: add_creditor_row(app, r),
        lambda r: delete_creditor_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.liabilities_rows.append(row)
    app.liabilities_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()
    app.capital_status_label.config(text="Добавлена строка кредиторской задолженности")

def add_creditor_row(app: Any, row: List[Any]) -> None:
    """Adds a creditor entry."""
    try:
        contractor = row[0].get()
        if not contractor:
            messagebox.showerror("Ошибка", "Введите контрагента.")
            app.capital_status_label.config(text="Ошибка: контрагент не указан")
            return
        amount = locale.atof(row[1].get() or '0')
        app.state.current_snapshot.balance.liabilities.creditors.append([contractor, amount])
        for state in app.liabilities_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")
        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен кредитор: {contractor}")
        app.capital_status_label.config(text=f"Добавлен кредитор: {contractor}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовое значение для суммы.")
        app.capital_status_label.config(text="Ошибка: некорректная сумма")

def delete_creditor_row(app: Any, row: List[Any]) -> None:
    """Deletes a creditor row."""
    contractor = row[0].get()
    app.state.current_snapshot.balance.liabilities.creditors = [
        c for c in app.state.current_snapshot.balance.liabilities.creditors if c[0] != contractor
    ]
    index = app.liabilities_rows.index(row)
    app.liabilities_rows.pop(index)
    app.liabilities_rows_state.pop(index)
    for widget in app.creditors_inner_frame.winfo_children():
        widget.destroy()
    creditors_headers = ["Контрагент", "Сумма, ₽"]
    creditors_header_frame = ttk.Frame(app.creditors_inner_frame)
    creditors_header_frame.pack(fill="x")
    for i, header in enumerate(creditors_headers):
        ttk.Label(creditors_header_frame, text=header).grid(row=0, column=i, padx=5, sticky="w")
    row_idx = 1
    for idx, (creditor, amount) in enumerate(app.state.current_snapshot.balance.liabilities.creditors):
        new_row = create_row(
            app.creditors_inner_frame,
            [{"type": "entry"}, {"type": "entry"}],
            lambda r: add_creditor_row(app, r),
            lambda r: delete_creditor_row(app, r),
            app.state.settings,
            row_idx=row_idx
        )
        new_row[0].insert(0, creditor)
        new_row[1].insert(0, str(amount))
        new_row[-1].config(background="green")
        app.liabilities_rows[idx] = new_row
        app.liabilities_rows_state[idx] = {"indicator": new_row[-1], "added": True, "used_in_calculation": True, "row": new_row}
        row_idx += 1
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text=f"Удалён кредитор: {contractor}")

def update_bank_accounts(app: Any) -> None:
    """Updates bank account entries in the UI."""
    for account, entry in app.bank_account_entries.items():
        entry.delete(0, tk.END)
        entry.insert(0, str(app.state.current_snapshot.balance.assets.bank_accounts[account]["fact"]))
    app.update_dashboard()
    app.update_tab_indicators()
    app.capital_status_label.config(text="Обновлены банковские счета")

def save_capital(app: Any) -> None:
    """Saves capital data."""
    try:
        # Обновляем банковские счета
        for account, entry in app.bank_account_entries.items():
            app.state.current_snapshot.balance.assets.bank_accounts[account]["fact"] = locale.atof(entry.get() or '0')

        # Обновляем наличные
        app.state.current_snapshot.cash.end = locale.atof(app.cash_entry.get() or '0')

        # Обновляем остатки на складах
        for stock, entry in app.stocks_entries.items():
            app.state.current_snapshot.balance.assets.stocks[stock]["fact"] = locale.atof(entry.get() or '0')

        # Обновляем зарплату
        app.state.current_snapshot.balance.liabilities.salary["fact"] = locale.atof(app.salary_entry.get() or '0')

        # Обновляем налоги
        for tax, entry in app.taxes_entries.items():
            app.state.current_snapshot.balance.liabilities.taxes[tax]["fact"] = locale.atof(entry.get() or '0')

        # Обновляем коммунальные услуги
        for utility, entry in app.utilities_entries.items():
            app.state.current_snapshot.balance.liabilities.utilities[utility]["fact"] = locale.atof(entry.get() or '0')

        # Обновляем аренду
        for rent, entry in app.rent_entries.items():
            app.state.current_snapshot.balance.liabilities.rent[rent]["fact"] = locale.atof(entry.get() or '0')

        # Обновляем бухгалтерию
        app.state.current_snapshot.balance.liabilities.accounting["fact"] = locale.atof(app.accounting_entry.get() or '0')

        # Обновляем прочих подрядчиков
        app.state.current_snapshot.balance.liabilities.other_contractors["fact"] = locale.atof(app.other_contractors_entry.get() or '0')

        # Обновляем кредитную линию
        app.state.current_snapshot.balance.liabilities.credit_line["fact"] = locale.atof(app.credit_line_entry.get() or '0')

        # Обновляем кредитную карту
        app.state.current_snapshot.balance.liabilities.credit_card["fact"] = locale.atof(app.credit_card_entry.get() or '0')

        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, "Данные капитализации сохранены")
        app.capital_status_label.config(text="Данные капитализации сохранены")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовые значения.")
        app.capital_status_label.config(text="Ошибка: некорректные значения")