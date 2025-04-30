import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment
import matplotlib.pyplot as plt
import numpy as np
from data_processing import filter_by_period, aggregate_month, aggregate_week

def export_report(app: "tk.Tk | ttk.Widget") -> None:
    """Экспортирует данные в Excel с листами 'Сводный' и 'Леджер налички'."""
    try:
        file_path = filedialog.asksaveasfilename(
            initialdir=app.last_dir,
            title="Сохранить отчёт",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        app.last_dir = os.path.dirname(file_path)

        # Создаём новую книгу Excel
        wb = openpyxl.Workbook()
        # Удаляем стандартный лист
        wb.remove(wb.active)

        # Лист "Выручка"
        ws_revenue = wb.create_sheet("Выручка")
        headers = ["Дата", "Заказчик", "Юрлицо", "Оборот (факт)", "Койко-дни (факт)", "Стоимость/день", "Себестоимость", "Наличные, ₽", "Безналичные, ₽"]
        for col, header in enumerate(headers, 1):
            cell = ws_revenue.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        row = 2
        for r in app.state.current_snapshot.revenue:
            ws_revenue.cell(row=row, column=1, value=r.date).number_format = "DD.MM.YYYY"
            ws_revenue.cell(row=row, column=2, value=r.customer)
            ws_revenue.cell(row=row, column=3, value=r.legal_entity)
            ws_revenue.cell(row=row, column=4, value=r.turnover_fact).number_format = "#,##0"
            ws_revenue.cell(row=row, column=5, value=r.beds_fact).number_format = "#,##0"
            ws_revenue.cell(row=row, column=6, value=r.cost).number_format = "#,##0"
            ws_revenue.cell(row=row, column=7, value=r.sebestoimost).number_format = "#,##0"
            ws_revenue.cell(row=row, column=8, value=r.cash_part).number_format = "#,##0"
            ws_revenue.cell(row=row, column=9, value=r.noncash_part).number_format = "#,##0"
            row += 1

        # Лист "Расходы"
        ws_expenses = wb.create_sheet("Расходы")
        headers = ["Дата", "Категория", "Контрагент", "Сумма, ₽", "Канал"]
        for col, header in enumerate(headers, 1):
            cell = ws_expenses.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        row = 2
        for e in app.state.current_snapshot.expenses:
            ws_expenses.cell(row=row, column=1, value=e.date).number_format = "DD.MM.YYYY"
            ws_expenses.cell(row=row, column=2, value=e.category)
            ws_expenses.cell(row=row, column=3, value=e.contractor)
            ws_expenses.cell(row=row, column=4, value=e.amount).number_format = "#,##0"
            ws_expenses.cell(row=row, column=5, value=e.channel)
            row += 1

        # Лист "Капитализация"
        ws_capital = wb.create_sheet("Капитализация")
        headers = ["Категория", "Подкатегория", "Значение, ₽"]
        for col, header in enumerate(headers, 1):
            cell = ws_capital.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        row = 2
        ws_capital.cell(row=row, column=1, value="Активы").font = Font(bold=True)
        row += 1
        for name, value in app.state.current_snapshot.balance.assets["bank_accounts"].items():
            ws_capital.cell(row=row, column=2, value=f"Счёт {name}")
            ws_capital.cell(row=row, column=3, value=value["fact"]).number_format = "#,##0"
            row += 1
        ws_capital.cell(row=row, column=2, value="Наличные")
        ws_capital.cell(row=row, column=3, value=app.state.current_snapshot.cash.end).number_format = "#,##0"
        row += 1
        for stock, value in app.state.current_snapshot.balance.assets["stocks"].items():
            ws_capital.cell(row=row, column=2, value=f"Склад {stock}")
            ws_capital.cell(row=row, column=3, value=value["fact"]).number_format = "#,##0"
            row += 1
        for debtor in app.state.current_snapshot.balance.assets["debtors"]:
            ws_capital.cell(row=row, column=2, value=f"Дебитор {debtor[0]}")
            ws_capital.cell(row=row, column=3, value=debtor[1]).number_format = "#,##0"
            row += 1
        for inv in app.state.current_snapshot.balance.assets["inventory"]:
            ws_capital.cell(row=row, column=2, value=f"Инвентарь {inv[0]} (Кол-во: {inv[2]})")
            ws_capital.cell(row=row, column=3, value=inv[1]).number_format = "#,##0"
            row += 1
        for vehicle in app.state.current_snapshot.balance.assets["vehicle"]:
            ws_capital.cell(row=row, column=2, value=f"Автотранспорт {vehicle[0]}")
            ws_capital.cell(row=row, column=3, value=vehicle[1]).number_format = "#,##0"
            row += 1

        row += 1
        ws_capital.cell(row=row, column=1, value="Пассивы").font = Font(bold=True)
        row += 1
        for creditor in app.state.current_snapshot.balance.liabilities["creditors"]:
            ws_capital.cell(row=row, column=2, value=f"Кредитор {creditor[0]}")
            ws_capital.cell(row=row, column=3, value=creditor[1]).number_format = "#,##0"
            row += 1
        ws_capital.cell(row=row, column=2, value="Зарплата")
        ws_capital.cell(row=row, column=3, value=app.state.current_snapshot.balance.liabilities["salary"]["fact"]).number_format = "#,##0"
        row += 1

        # Лист "Леджер налички"
        ws_ledger = wb.create_sheet("Леджер налички")
        headers = ["Дата", "Источник", "Сумма, ₽", "Описание"]
        for col, header in enumerate(headers, 1):
            cell = ws_ledger.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        row = 2
        for _, row_data in app.owl_agent.transactions_df.iterrows():
            if row_data["Категория"] == "Денежные средства":
                ws_ledger.cell(row=row, column=1, value=row_data["Дата"]).number_format = "DD.MM.YYYY"
                ws_ledger.cell(row=row, column=2, value="Банковская выписка")
                ws_ledger.cell(row=row, column=3, value=row_data["Сумма"]).number_format = "#,##0"
                ws_ledger.cell(row=row, column=4, value=row_data["Назначение платежа"])
                row += 1

        # Лист "Сводный"
        ws_summary = wb.create_sheet("Сводный")
        headers = ["Метрика", "Значение"]
        for col, header in enumerate(headers, 1):
            cell = ws_summary.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        # Ключевые метрики
        period_dict = app.state.settings["period"]
        filtered_revenue = filter_by_period(
            [r.__dict__ for r in app.state.current_snapshot.revenue], period_dict
        )
        filtered_expenses = filter_by_period(
            [e.__dict__ for e in app.state.current_snapshot.expenses], period_dict
        )
        total_revenue = sum(row["turnover_fact"] for row in filtered_revenue)
        total_expenses = sum(item["amount"] for item in filtered_expenses)
        profit = total_revenue - total_expenses

        # Рассчитываем капитализацию
        total_assets = sum(item["fact"] for item in app.state.current_snapshot.balance.assets["bank_accounts"].values()) + \
                       app.state.current_snapshot.cash.end + \
                       sum(row[1] for row in app.state.current_snapshot.balance.assets["debtors"]) + \
                       sum(row[4] for row in app.state.current_snapshot.balance.assets["equipment"]) + \
                       sum(row[1] for row in app.state.current_snapshot.balance.assets["inventory"]) + \
                       sum(row[1] for row in app.state.current_snapshot.balance.assets["vehicle"]) + \
                       sum(item["fact"] for item in app.state.current_snapshot.balance.assets["stocks"].values())
        total_liabilities = sum(row[1] for row in app.state.current_snapshot.balance.liabilities["creditors"] if row[1] > 0) + \
                            app.state.current_snapshot.balance.liabilities["salary"]["fact"] + \
                            sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities["taxes"].values()) + \
                            sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities["utilities"].values()) + \
                            sum(item["fact"] for item in app.state.current_snapshot.balance.liabilities["rent"].values()) + \
                            app.state.current_snapshot.balance.liabilities["accounting"]["fact"] + \
                            app.state.current_snapshot.balance.liabilities["other_contractors"]["fact"] + \
                            app.state.current_snapshot.balance.liabilities["credit_line"]["fact"] + \
                            app.state.current_snapshot.balance.liabilities["credit_card"]["fact"]
        capital = total_assets - total_liabilities

        # Рассчитываем Δ капитализации
        delta_cap = None
        try:
            end_date = datetime.strptime(period_dict["end_date"], "%Y-%m-%d")
            prev_end_date = (end_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_start_date = prev_end_date[:8] + "01"
            prev_period_key = f"{prev_start_date}_{prev_end_date}"
            prev_snapshot = app.state.PeriodSnapshot.load_from_file(os.path.join("periods", f"{prev_period_key}.json"))
            prev_total_assets = sum(item["fact"] for item in prev_snapshot.balance.assets["bank_accounts"].values()) + \
                                prev_snapshot.cash.end + \
                                sum(row[1] for row in prev_snapshot.balance.assets["debtors"]) + \
                                sum(row[4] for row in prev_snapshot.balance.assets["equipment"]) + \
                                sum(row[1] for row in prev_snapshot.balance.assets["inventory"]) + \
                                sum(row[1] for row in prev_snapshot.balance.assets["vehicle"]) + \
                                sum(item["fact"] for item in prev_snapshot.balance.assets["stocks"].values())
            prev_total_liabilities = sum(row[1] for row in prev_snapshot.balance.liabilities["creditors"] if row[1] > 0) + \
                                     prev_snapshot.balance.liabilities["salary"]["fact"] + \
                                     sum(item["fact"] for item in prev_snapshot.balance.liabilities["taxes"].values()) + \
                                     sum(item["fact"] for item in prev_snapshot.balance.liabilities["utilities"].values()) + \
                                     sum(item["fact"] for item in prev_snapshot.balance.liabilities["rent"].values()) + \
                                     prev_snapshot.balance.liabilities["accounting"]["fact"] + \
                                     prev_snapshot.balance.liabilities["other_contractors"]["fact"] + \
                                     prev_snapshot.balance.liabilities["credit_line"]["fact"] + \
                                     prev_snapshot.balance.liabilities["credit_card"]["fact"]
            prev_capital = prev_total_assets - prev_total_liabilities
            delta_cap = capital - prev_capital
        except Exception:
            delta_cap = None

        # Рассчитываем среднюю маржу
        margins = []
        for row in filtered_revenue:
            if row["legal_entity"] == "ООО" and row["turnover_fact"] > 0:
                margin = (row["turnover_fact"] - row["sebestoimost"] * row["beds_fact"]) / row["turnover_fact"] * 100
                margins.append(margin)
        avg_margin = sum(margins) / len(margins) if margins else 0

        # Заполняем метрики
        metrics = [
            ("Выручка, ₽", total_revenue),
            ("Расходы, ₽", total_expenses),
            ("Прибыль, ₽", profit),
            ("Капитализация, ₽", capital),
            ("Δ капитализации, ₽", delta_cap if delta_cap is not None else "-"),
            ("Средняя рентабельность, %", avg_margin)
        ]

        row = 2
        for name, value in metrics:
            ws_summary.cell(row=row, column=1, value=name)
            cell = ws_summary.cell(row=row, column=2, value=value)
            if isinstance(value, (int, float)) and name != "Средняя рентабельность, %":
                cell.number_format = "#,##0"
            elif name == "Средняя рентабельность, %":
                cell.number_format = "0.00%"
            row += 1

        # Создаём график прибыли по периодам
        period_dict = app.state.settings["period"]
        filtered_revenue = filter_by_period(
            [r.__dict__ for r in app.state.current_snapshot.revenue], period_dict
        )
        filtered_expenses = filter_by_period(
            [e.__dict__ for e in app.state.current_snapshot.expenses], period_dict
        )
        periods = sorted(set([r["date"][:7] for r in filtered_revenue] + [e["date"][:7] for e in filtered_expenses]))
        profits = []
        for period in periods:
            revenue = sum(r["turnover_fact"] for r in filtered_revenue if r["date"][:7] == period)
            expenses = sum(e["amount"] for e in filtered_expenses if e["date"][:7] == period)
            profits.append(revenue - expenses)

        # Создаём график
        plt.figure(figsize=(8, 4))
        plt.plot(periods, profits, marker='o', color='#1e88e5', label='Прибыль, ₽')
        plt.title("Прибыль по периодам", fontsize=12)
        plt.xlabel("Период")
        plt.ylabel("Прибыль, ₽")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        chart_path = "profit_chart.png"
        plt.savefig(chart_path)
        plt.close()

        # Вставляем график в Excel
        img = openpyxl.drawing.image.Image(chart_path)
        img.anchor = "A10"
        ws_summary.add_image(img)

        # Устанавливаем ширину столбцов
        for ws in [ws_revenue, ws_expenses, ws_capital, ws_ledger, ws_summary]:
            for col in range(1, ws.max_column + 1):
                column_letter = get_column_letter(col)
                ws.column_dimensions[column_letter].width = 20

        # Сохраняем файл
        wb.save(file_path)
        os.remove(chart_path)  # Удаляем временный файл графика
        app.ai_text.insert(tk.END, f"Owl: Отчёт успешно экспортирован в {file_path}\n")
        app.ai_text.see(tk.END)
    except Exception as e:
        app.ai_text.insert(tk.END, f"Owl: Ошибка экспорта: {e}\n")
        app.ai_text.see(tk.END)