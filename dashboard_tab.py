import tkinter as tk
from tkinter import ttk, messagebox
import locale
from typing import Any
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from data_processing import load_snapshot, save_snapshot, filter_by_period
import matplotlib.pyplot as plt
import numpy as np

def build_dashboard(app: Any) -> None:
    """Creates the Dashboard tab with summary information."""
    locale.setlocale(locale.LC_ALL, '')
    for widget in app.tab_dashboard.winfo_children():
        widget.destroy()

    dashboard_frame = ttk.Frame(app.tab_dashboard, padding=10)
    dashboard_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")

    # Период
    period_frame = ttk.LabelFrame(dashboard_frame, text="Период", padding=5)
    period_frame.pack(fill="x", pady=5)

    ttk.Button(period_frame, text="Месячная ревизия", command=lambda: set_monthly_period(app)).pack(side="left", padx=5)

    ttk.Label(period_frame, text="Начало периода:").pack(side="left", padx=5)
    app.start_date = DateEntry(period_frame, width=12, date_pattern="yyyy-mm-dd")
    app.start_date.pack(side="left", padx=5)
    app.start_date.set_date(app.state.settings.get("period", {}).get("start_date", "2025-04-01"))

    ttk.Label(period_frame, text="Конец периода:").pack(side="left", padx=5)
    app.end_date = DateEntry(period_frame, width=12, date_pattern="yyyy-mm-dd")
    app.end_date.pack(side="left", padx=5)
    app.end_date.set_date(app.state.settings.get("period", {}).get("end_date", "2025-04-30"))

    ttk.Button(period_frame, text="Применить", command=lambda: apply_period(app)).pack(side="left", padx=5)
    ttk.Button(period_frame, text="Сохранить период", command=lambda: save_current_period(app)).pack(side="left", padx=5)
    ttk.Button(period_frame, text="Загрузить предыдущий период", command=lambda: load_previous_period(app)).pack(side="left", padx=5)

    # Общие показатели
    summary_frame = ttk.LabelFrame(dashboard_frame, text="Общие показатели", padding=5)
    summary_frame.pack(fill="x", pady=5)

    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    filtered_revenue = filter_by_period([r.__dict__ for r in app.state.current_snapshot.revenue], period_dict)
    filtered_expenses = filter_by_period([e.__dict__ for e in app.state.current_snapshot.expenses], period_dict)
    total_revenue_ooo = sum(row["turnover_fact"] for row in filtered_revenue if row["legal_entity"] == "ООО")
    total_revenue_ip = sum(row["turnover_fact"] for row in filtered_revenue if row["legal_entity"] == "ИП")
    total_expenses = sum(item["amount"] for item in filtered_expenses)
    profit = total_revenue_ooo + total_revenue_ip - total_expenses

    ttk.Label(summary_frame, text=f"Выручка ООО: {total_revenue_ooo:,.0f} руб").pack(anchor="w")
    ttk.Label(summary_frame, text=f"Выручка ИП (буфеты): {total_revenue_ip:,.0f} руб").pack(anchor="w")
    ttk.Label(summary_frame, text=f"Общие расходы: {total_expenses:,.0f} руб").pack(anchor="w")
    ttk.Label(summary_frame, text=f"Прибыль: {profit:,.0f} руб").pack(anchor="w")

    # Структура расходов
    expenses_frame = ttk.LabelFrame(dashboard_frame, text="Структура расходов", padding=5)
    expenses_frame.pack(fill="x", pady=5)

    cash_expenses = sum(item["amount"] for item in filtered_expenses if item["channel"] == "cash")
    noncash_expenses = sum(item["amount"] for item in filtered_expenses if item["channel"] == "noncash")

    ttk.Label(expenses_frame, text=f"Наличные расходы: {cash_expenses:,.0f} руб").pack(anchor="w")
    ttk.Label(expenses_frame, text=f"Безналичные расходы: {noncash_expenses:,.0f} руб").pack(anchor="w")

    # Баланс наличных
    cash_balance_frame = ttk.LabelFrame(dashboard_frame, text="Баланс наличных", padding=5)
    cash_balance_frame.pack(fill="x", pady=5)

    cash_available = app.state.current_snapshot.cash.start + app.state.current_snapshot.cash.income - app.state.current_snapshot.cash.expenses
    ttk.Label(cash_balance_frame, text=f"Начальный остаток: {app.state.current_snapshot.cash.start:,.0f} руб").pack(anchor="w")
    ttk.Label(cash_balance_frame, text=f"Поступления: {app.state.current_snapshot.cash.income:,.0f} руб").pack(anchor="w")
    ttk.Label(cash_balance_frame, text=f"Расходы: {app.state.current_snapshot.cash.expenses:,.0f} руб").pack(anchor="w")
    ttk.Label(cash_balance_frame, text=f"Конечный остаток: {app.state.current_snapshot.cash.end:,.0f} руб").pack(anchor="w")
    ttk.Label(cash_balance_frame, text=f"Доступно для распределения: {cash_available:,.0f} руб").pack(anchor="w")

    # Капитализация
    capital_frame = ttk.LabelFrame(dashboard_frame, text="Капитализация", padding=5)
    capital_frame.pack(fill="x", pady=5)

    total_assets = sum(item["fact"] for item in app.state.current_snapshot.balance.assets.bank_accounts.values()) + \
                   app.state.current_snapshot.cash.end + \
                   sum(row[1] for row in app.state.current_snapshot.balance.assets.debtors) + \
                   sum(row[4] for row in app.state.current_snapshot.balance.assets.equipment) + \
                   sum(row[1] for row in app.state.current_snapshot.balance.assets.inventory) + \
                   sum(row[1] for row in app.state.current_snapshot.balance.assets.vehicle) + \
                   sum(item["fact"] for item in app.state.current_snapshot.balance.assets.stocks.values())

    total_liabilities = sum(row[1] for row in app.state.current_snapshot.balance.liabilities.creditors if row[1] > 0) + \
                        app.state.current_snapshot.balance.liabilities.salary["fact"] + \
                        sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities.taxes.values()) + \
                        sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities.utilities.values()) + \
                        sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities.rent.values()) + \
                        app.state.current_snapshot.balance.liabilities.accounting["fact"] + \
                        app.state.current_snapshot.balance.liabilities.other_contractors["fact"] + \
                        app.state.current_snapshot.balance.liabilities.credit_line["fact"] + \
                        app.state.current_snapshot.balance.liabilities.credit_card["fact"]

    capital = total_assets - total_liabilities

    delta_cap = None
    prev_period_key = None
    try:
        end_date = datetime.strptime(period_dict["end_date"], "%Y-%m-%d")
        prev_end_date = (end_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
        prev_start_date = prev_end_date[:8] + "01"
        prev_period_key = f"{prev_start_date}_{prev_end_date}"
        prev_snapshot = load_snapshot(prev_period_key)
        prev_total_assets = sum(item["fact"] for item in prev_snapshot.balance.assets.bank_accounts.values()) + \
                            prev_snapshot.cash.end + \
                            sum(row[1] for row in prev_snapshot.balance.assets.debtors) + \
                            sum(row[4] for row in prev_snapshot.balance.assets.equipment) + \
                            sum(row[1] for row in prev_snapshot.balance.assets.inventory) + \
                            sum(row[1] for row in prev_snapshot.balance.assets.vehicle) + \
                            sum(item["fact"] for item in prev_snapshot.balance.assets.stocks.values())
        prev_total_liabilities = sum(row[1] for row in prev_snapshot.balance.liabilities.creditors if row[1] > 0) + \
                                 prev_snapshot.balance.liabilities.salary["fact"] + \
                                 sum(item["fact"] for item in prev_snapshot.balance.liabilities.taxes.values()) + \
                                 sum(item["fact"] for item in prev_snapshot.balance.liabilities.utilities.values()) + \
                                 sum(item["fact"] for item in prev_snapshot.balance.liabilities.rent.values()) + \
                                 prev_snapshot.balance.liabilities.accounting["fact"] + \
                                 prev_snapshot.balance.liabilities.other_contractors["fact"] + \
                                 prev_snapshot.balance.liabilities.credit_line["fact"] + \
                                 prev_snapshot.balance.liabilities.credit_card["fact"]
        prev_capital = prev_total_assets - prev_total_liabilities
        delta_cap = capital - prev_capital
    except Exception:
        delta_cap = None

    ttk.Label(capital_frame, text=f"Активы: {total_assets:,.0f} руб").pack(anchor="w")
    ttk.Label(capital_frame, text=f"Пассивы: {total_liabilities:,.0f} руб").pack(anchor="w")
    ttk.Label(capital_frame, text=f"Капитализация: {capital:,.0f} руб").pack(anchor="w")
    ttk.Label(capital_frame, text=f"Δ капитализации: {delta_cap:,.0f} руб" if delta_cap is not None else "Δ капитализации: -").pack(anchor="w")

    if delta_cap is not None and abs(delta_cap - profit) > 0.01:
        ttk.Label(capital_frame, text=f"Внимание: Δ капитализации ({delta_cap:,.0f} руб) не соответствует прибыли ({profit:,.0f} руб)", foreground="red").pack(anchor="w")
    elif delta_cap is not None:
        ttk.Label(capital_frame, text="Δ капитализации соответствует прибыли", foreground="green").pack(anchor="w")

    # График сравнения капитализации и прибыли
    if delta_cap is not None:
        ttk.Button(capital_frame, text="Показать график сравнения", command=lambda: show_capital_profit_graph(app, capital, delta_cap, profit)).pack(anchor="w")

    # Кнопки для графиков
    buttons_frame = ttk.Frame(dashboard_frame)
    buttons_frame.pack(fill="x", pady=10)
    buttons_frame.grid_columnconfigure((0, 1), weight=1)

    ttk.Button(buttons_frame, text="График выручки", command=lambda: app.show_chart("revenue")).grid(row=0, column=0, padx=5, sticky="ew")
    ttk.Button(buttons_frame, text="График расходов", command=lambda: app.show_chart("expenses")).grid(row=0, column=1, padx=5, sticky="ew")

def set_monthly_period(app: Any) -> None:
    """Sets the period to the current month."""
    today = datetime.now()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = (today.replace(day=1, month=today.month+1) - timedelta(days=1)).strftime("%Y-%m-%d") if today.month < 12 else f"{today.year}-12-31"
    app.start_date.set_date(start_date)
    app.end_date.set_date(end_date)
    apply_period(app)

def apply_period(app: Any) -> None:
    """Applies the selected period and updates the dashboard."""
    start_date = app.start_date.get()
    end_date = app.end_date.get()

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            app.status_label.config(text="Ошибка: Дата начала не может быть позже даты окончания")
            return
    except ValueError:
        app.status_label.config(text="Ошибка: Некорректный формат даты")
        return

    app.state.settings["period"]["start_date"] = start_date
    app.state.settings["period"]["end_date"] = end_date
    period_key = f"{start_date}_{end_date}"
    app.current_snapshot.period_key = period_key
    app.save_settings()

    try:
        app.state.current_snapshot = load_snapshot(period_key)
    except FileNotFoundError:
        app.state.current_snapshot = PeriodSnapshot()
        app.state.current_snapshot.period_key = period_key

    app.update_dashboard()
    from revenue_tab import build_revenue
    from expenses_tab import build_expenses
    from capital_tab import build_capital
    from debtors_creditors_tab import build_creditors, build_debtors
    from equipment_tab import build_equipment
    build_revenue(app)
    build_expenses(app)
    build_capital(app)
    build_creditors(app)
    build_debtors(app)
    build_equipment(app)
    app.update_tab_indicators()
    app.status_label.config(text=f"Период установлен: {start_date} - {end_date}")

def save_current_period(app: Any) -> None:
    """Saves the current period snapshot."""
    period_key = app.current_snapshot.period_key
    save_snapshot(app.state.current_snapshot, period_key)
    app.status_label.config(text=f"Период {period_key} сохранен")

def load_previous_period(app: Any) -> None:
    """Loads the previous period snapshot."""
    period_dict = app.state.settings.get("period", {"start_date": "2025-04-01", "end_date": "2025-04-30"})
    try:
        end_date = datetime.strptime(period_dict["end_date"], "%Y-%m-%d")
        prev_end_date = (end_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
        prev_start_date = prev_end_date[:8] + "01"
        prev_period_key = f"{prev_start_date}_{prev_end_date}"
        app.state.current_snapshot = load_snapshot(prev_period_key)
        app.start_date.set_date(prev_start_date)
        app.end_date.set_date(prev_end_date)
        app.state.settings["period"]["start_date"] = prev_start_date
        app.state.settings["period"]["end_date"] = prev_end_date
        app.current_snapshot.period_key = prev_period_key
        app.save_settings()
        app.update_dashboard()
        from revenue_tab import build_revenue
        from expenses_tab import build_expenses
        from capital_tab import build_capital
        from debtors_creditors_tab import build_creditors, build_debtors
        from equipment_tab import build_equipment
        build_revenue(app)
        build_expenses(app)
        build_capital(app)
        build_creditors(app)
        build_debtors(app)
        build_equipment(app)
        app.update_tab_indicators()
        app.status_label.config(text=f"Загружен предыдущий период: {prev_start_date} - {prev_end_date}")
    except Exception as e:
        app.status_label.config(text=f"Ошибка загрузки предыдущего периода: {e}")

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