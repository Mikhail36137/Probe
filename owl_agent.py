import os
import pandas as pd
import json
import logging
import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, messagebox
from threading import Thread
import queue
import locale
import re
from dateutil import parser
from state import AppState, ExpenseRow
from anomaly_engine import detect_anomalies

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

EXPENSE_CATEGORIES = {
    'Продукты': ['товар', 'питание', 'mcc5411', 'pyaterochka'],
    'Транспорт': ['бензин', 'такси', 'билет', 'mcc5541'],
    'Коммунальные': ['электроэнергия', 'водоснабжение', 'коммунальные'],
    'Развлечения': ['кафе', 'ресторан', 'кино', 'театр'],
    'Аренда': ['аренда'],
    'Налоги': ['енп', 'ндфл', 'пфр', 'усн'],
    'Услуги_Медицинские': ['медицинские услуги', 'больница', 'аптека'],
    'Услуги_Юридические': ['юридические услуги', 'нотариус', 'Адвокат'],
    'Услуги_Образовательные': ['обучение', 'курсы', 'университет'],
    'Услуги_Комиссии': ['комиссии', 'банковские услуги'],
    'Услуги_Прочее': ['услуг'],
    'Внутрифирменные': ['внутрифирменное'],
    'Зарплата': ['заработной плате', 'аванс', 'зарплата'],
    'Денежные средства': ['выдача наличных', 'cash withdrawal', 'снятие наличных', 'зачисление от ИП', 'банкомат', 'atm withdrawal'],
    'Прочее': []
}

OVERRIDE_CATEGORIES = {}

def load_override_categories() -> None:
    global OVERRIDE_CATEGORIES
    try:
        with open("override_categories.json", "r", encoding="utf-8") as f:
            OVERRIDE_CATEGORIES = json.load(f)
        logging.info("Успешно загружены категории из override_categories.json")
    except FileNotFoundError:
        OVERRIDE_CATEGORIES = {}
        logging.warning("Файл override_categories.json не найден, используется пустой словарь")
    except Exception as e:
        logging.error(f"Ошибка при загрузке override_categories.json: {e}")
        OVERRIDE_CATEGORIES = {}

def save_override_categories() -> None:
    try:
        with open("override_categories.json", "w", encoding="utf-8") as f:
            json.dump(OVERRIDE_CATEGORIES, f, ensure_ascii=False, indent=4)
        logging.info("Категории успешно сохранены в override_categories.json")
    except Exception as e:
        logging.error(f"Ошибка при сохранении override_categories.json: {e}")

def normalize_description(description: str) -> str:
    if not isinstance(description, str) or pd.isna(description):
        return ''
    return ' '.join(description.lower().strip().split()).replace('\\', '\\\\')

def categorize_expense(description: str, contractor: str = None) -> str:
    normalized_desc = normalize_description(description)
    contractor = normalize_description(contractor) if contractor else ''
    key = normalized_desc
    logging.debug(f"Сформирован ключ для категоризации: {key}")

    if key in OVERRIDE_CATEGORIES:
        logging.debug(f"Найдена категория в OVERRIDE_CATEGORIES: {OVERRIDE_CATEGORIES[key]}")
        return OVERRIDE_CATEGORIES[key]

    for category, keywords in EXPENSE_CATEGORIES.items():
        if any(keyword in normalized_desc for keyword in keywords):
            OVERRIDE_CATEGORIES[key] = category
            logging.debug(f"Категория определена по ключевым словам: {category}")
            return category

    OVERRIDE_CATEGORIES[key] = 'Прочее'
    logging.debug(f"Категория не найдена, установлена по умолчанию: Прочее")
    return 'Прочее'

class OwlAgent:
    def __init__(self):
        self.app: Optional[Any] = None
        self.result_queue = queue.Queue()
        self.transactions_df = None
        self.all_expense_categories = list(set(EXPENSE_CATEGORIES.keys()))
        load_override_categories()

    def generate_response(self, user_input: str) -> str:
        user_input_lower = user_input.lower().strip()
        if user_input_lower == "загрузи выписку":
            return self.load_dds()
        elif user_input_lower == "проверь выручку":
            return self.check_revenue()
        elif user_input_lower == "проверь расходы":
            return self.check_expenses()
        elif user_input_lower == "проверь капитализацию":
            return self.check_capital()
        elif user_input_lower == "покажи график выручки":
            self.app.show_chart("revenue")
            return "График выручки отображён на вкладке Dashboard."
        elif user_input_lower == "покажи график расходов":
            self.app.show_chart("expenses")
            return "График структуры расходов отображён на вкладке Dashboard."
        else:
            return f"🧠 Owl: Я пока не могу обработать запрос '{user_input}'. Введите команду, например, 'загрузи выписку'."

    def load_dds(self) -> str:
        try:
            file_path = filedialog.askopenfilename(
                initialdir=self.app.last_dir,
                title="Загрузите выписку ДДС",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not file_path:
                return "Загрузка отменена."

            self.app.loading_label = ttk.Label(self.app.root, text="Загрузка… ⏳")
            self.app.loading_label.pack()

            thread = Thread(target=self._load_dds_thread, args=(file_path,))
            thread.start()

            self.app.root.after(100, self._check_load_result)
            return "Загрузка начата..."
        except Exception as e:
            return f"Не удалось загрузить выписку: {e}"

    def _load_dds_thread(self, file_path: str) -> None:
        try:
            locale.setlocale(locale.LC_ALL, '')
            header_df = pd.read_excel(file_path, nrows=15, header=None)
            logging.debug(f"Содержимое шапки (первые 15 строк):\n{header_df.to_string()}")

            incoming_value = header_df.iloc[6, 1]
            outgoing_value = header_df.iloc[7, 1]
            logging.debug(f"Сырое значение входящего остатка (R7C2): {incoming_value}")
            logging.debug(f"Сырое значение исходящего остатка (R8C2): {outgoing_value}")

            try:
                incoming_balance = float(str(incoming_value).replace(' ', '').replace(',', '.')) if pd.notna(incoming_value) else 0.0
            except (ValueError, TypeError) as e:
                logging.error(f"Ошибка преобразования входящего остатка: {incoming_value}, ошибка: {e}")
                self.app.owl_respond_command(
                    f"Owl: Внимание! Некорректное значение входящего остатка: '{incoming_value}'. Установлено значение 0.0."
                )
                incoming_balance = 0.0

            try:
                outgoing_balance = float(str(outgoing_value).replace(' ', '').replace(',', '.')) if pd.notna(outgoing_value) else 0.0
            except (ValueError, TypeError) as e:
                logging.error(f"Ошибка преобразования исходящего остатка: {outgoing_value}, ошибка: {e}")
                self.app.owl_respond_command(
                    f"Owl: Внимание! Некорректное значение исходящего остатка: '{outgoing_value}'. Установлено значение 0.0."
                )
                outgoing_balance = 0.0

            period_rows = header_df[header_df.apply(lambda row: row.str.contains("За период|Period", case=False, na=False).any(), axis=1)]
            if period_rows.empty:
                raise ValueError("Файл не содержит строку 'За период' или 'Period' в первых 15 строках. Проверьте формат файла.")
            
            period_row = period_rows.iloc[0]
            period_data = None
            for col in period_row.index:
                value = period_row[col]
                if isinstance(value, str) and (re.search(r"\d{2}\.\d{2}\.\d{4}", value) or re.search(r"\d{2}/\d{2}/\d{4}", value)):
                    period_data = value
                    break
            if not period_data:
                logging.debug(f"Значение строки 'За период': {period_row.to_string()}")
                raise ValueError("Не удалось найти корректное значение периода в строке 'За период'. Ожидаются даты в формате 'ДД.ММ.ГГГГ' или 'ДД/ММ/ГГГГ'.")

            date_pattern = r"(\d{2}\.\d{2}\.\d{4}|\d{2}/\d{2}/\d{4})"
            dates = re.findall(date_pattern, period_data)
            if len(dates) >= 2:
                period_start = dates[0]
                period_end = dates[1]
            else:
                try:
                    parsed_dates = [parser.parse(d, dayfirst=True) for d in period_data.split('-')]
                    if len(parsed_dates) == 2:
                        period_start = parsed_dates[0].strftime("%d.%m.%Y")
                        period_end = parsed_dates[1].strftime("%d.%m.%Y")
                    else:
                        raise ValueError("Не удалось разобрать даты периода. Ожидаются две даты, разделённые дефисом или пробелом.")
                except Exception as e:
                    logging.debug(f"Ошибка парсинга периода '{period_data}': {e}")
                    raise ValueError(f"Некорректный формат периода: '{period_data}'. Ожидаются даты в формате 'ДД.ММ.ГГГГ - ДД.ММ.ГГГГ' или 'ДД/ММ/ГГГГ to ДД/ММ/ГГГГ'.")

            credit_turnover_row = header_df[header_df.apply(lambda row: row.str.contains("Обороты кредит|Кредитовые обороты|Credit Turnover|Приходы|Receipts|Credit", case=False, na=False).any(), axis=1)]
            debit_turnover_row = header_df[header_df.apply(lambda row: row.str.contains("Обороты дебет|Дебетовые обороты|Debit Turnover|Расходы|Expenses|Debit", case=False, na=False).any(), axis=1)]
            credit_value = credit_turnover_row.iloc[0, credit_turnover_row.columns.get_loc(credit_turnover_row.index[0]) + 1] if not credit_turnover_row.empty else 0.0
            debit_value = debit_turnover_row.iloc[0, debit_turnover_row.columns.get_loc(debit_turnover_row.index[0]) + 1] if not debit_turnover_row.empty else 0.0
            logging.debug(f"Значение кредитовых оборотов: {credit_value}")
            logging.debug(f"Значение дебетовых оборотов: {debit_value}")
            try:
                credit_turnover = float(str(credit_value).replace(' ', '').replace(',', '.')) if pd.notna(credit_value) else 0.0
            except (ValueError, TypeError):
                self.app.owl_respond_command(
                    f"Owl: Внимание! Некорректное значение кредитовых оборотов: '{credit_value}'. Установлено значение 0.0."
                )
                credit_turnover = 0.0
            try:
                debit_turnover = float(str(debit_value).replace(' ', '').replace(',', '.')) if pd.notna(debit_value) else 0.0
            except (ValueError, TypeError):
                self.app.owl_respond_command(
                    f"Owl: Внимание! Некорректное значение дебетовых оборотов: '{debit_value}'. Установлено значение 0.0."
                )
                debit_turnover = 0.0

            account_type = "ООО"
            if credit_turnover != 0.0 or debit_turnover != 0.0:
                calculated_outgoing = incoming_balance + credit_turnover - debit_turnover
                if abs(calculated_outgoing - outgoing_balance) > 0.01:
                    self.app.owl_respond_command(
                        f"Owl: Внимание! Проверочная процедура не прошла: Входящий остаток ({incoming_balance:,.2f}) + Приходы ({credit_turnover:,.2f}) - Расходы ({debit_turnover:,.2f}) = {calculated_outgoing:,.2f}, но Исходящий остаток = {outgoing_balance:,.2f}. Возможен пропуск данных."
                    )

            self.app.state.current_snapshot.balance.assets.bank_accounts[account_type]["fact"] = outgoing_balance
            from capital_tab import update_bank_accounts
            update_bank_accounts(self.app)

            df = pd.read_excel(file_path, skiprows=9, header=0, decimal=',')
            actual_columns = df.columns.tolist()
            logging.debug(f"Прочитанные заголовки столбцов: {actual_columns}")

            expected_columns = [
                'Дата', 'Номер документа', 'Дебет', 'Кредит', 'Контрагент', 'Наименование',
                'ИНН', 'КПП', 'Счёт', 'БИК', 'Назначение платежа', 'Наименование банка',
                'Код дебитора', 'Тип документа'
            ]

            num_columns = len(actual_columns)
            if num_columns < len(expected_columns):
                for i in range(num_columns, len(expected_columns)):
                    df[expected_columns[i]] = pd.NA
            elif num_columns > len(expected_columns):
                df = df.iloc[:, :len(expected_columns)]

            df.columns = expected_columns[:len(df.columns)]
            required_columns = ['Дебет', 'Кредит', 'Назначение платежа', 'Контрагент']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("В файле должны быть колонки 'Дебет', 'Кредит', 'Назначение платежа' и 'Контрагент'")

            df['Дебет'] = pd.to_numeric(df['Дебет'], errors='coerce').round(2)
            df['Кредит'] = pd.to_numeric(df['Кредит'], errors='coerce').round(2)
            df['Назначение платежа'] = df['Назначение платежа'].astype(str).fillna("")

            logging.debug(f"Первые несколько строк столбца 'Назначение платежа': {df['Назначение платежа'].head().tolist()}")

            expenses_df = df[df['Дебет'].notna() & (df['Дебет'] > 0)].copy()
            expenses_df['Тип'] = 'Расход'
            expenses_df['Сумма'] = expenses_df['Дебет']
            expenses_df['Категория'] = expenses_df.apply(
                lambda row: categorize_expense(row['Назначение платежа'], row['Контрагент']), axis=1
            )

            cash_withdrawal_total = 0.0
            for _, row in expenses_df.iterrows():
                description = str(row.get("Назначение платежа", "")).lower()
                if any(keyword in description for keyword in EXPENSE_CATEGORIES['Денежные средства']):
                    amount = row["Дебет"]
                    cash_withdrawal_total += amount

            self.app.state.current_snapshot.cash.income += cash_withdrawal_total

            self.transactions_df = expenses_df
            self.app.statement_period = {"start": period_start, "end": period_end}
            self.app.last_dir = os.path.dirname(file_path)
            self.result_queue.put(("success", file_path))
        except Exception as e:
            self.result_queue.put(("error", str(e)))

    def _check_load_result(self) -> None:
        try:
            result_type, result = self.result_queue.get_nowait()
            self.app.loading_label.destroy()
            if result_type == "success":
                self.app.save_settings()
                self._show_edit_window()
                cash_available = self.app.state.current_snapshot.cash.start + self.app.state.current_snapshot.cash.income - self.app.state.current_snapshot.cash.expenses
                self.app.owl_respond_command(f"Owl: Выписка загружена. Доступно наличных для распределения: {cash_available:,.0f} руб. Перейдите во вкладку 'Расходы' для распределения.")
            else:
                self.app.owl_respond_command(f"Owl: Не удалось загрузить выписку: {result}")
        except queue.Empty:
            self.app.root.after(100, self._check_load_result)

    def _show_edit_window(self):
        edit_window = Toplevel(self.app.root)
        edit_window.title("Просмотр и редактирование категорий")
        edit_window.geometry("1400x400")

        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(main_frame)
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        scrollable_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def update_frame_size(event):
            canvas_width = event.width
            canvas_height = event.height
            button_height = 40
            available_height = canvas_height - button_height
            canvas.itemconfig(window_id, width=canvas_width, height=max(available_height, scrollable_frame.winfo_reqheight()))

        canvas.bind("<Configure>", update_frame_size)

        def update_scrollregion():
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", lambda e: update_scrollregion())

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree = ttk.Treeview(scrollable_frame, columns=('Дата', 'Контрагент', 'Сумма', 'Назначение', 'Тип', 'Категория'), show='headings')
        tree.heading('Дата', text='Дата')
        tree.heading('Контрагент', text='Контрагент')
        tree.heading('Сумма', text='Сумма')
        tree.heading('Назначение', text='Назначение платежа')
        tree.heading('Тип', text='Тип')
        tree.heading('Категория', text='Категория')

        tree.column('Дата', width=100)
        tree.column('Контрагент', width=200)
        tree.column('Сумма', width=100)
        tree.column('Назначение', width=400)
        tree.column('Тип', width=100)
        tree.column('Категория', width=200)

        tree.grid(row=0, column=0, sticky="nsew")
        scrollable_frame.grid_rowconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        for i, row in self.transactions_df.iterrows():
            contractor = str(row['Контрагент']) if pd.notna(row['Контрагент']) else ""
            description = str(row['Назначение платежа']) if pd.notna(row['Назначение платежа']) else ""
            tree.insert('', 'end', iid=i, values=(
                row['Дата'], contractor, row['Сумма'], description, row['Тип'], row['Категория']
            ))

        def scroll_treeview(event):
            widget_under_cursor = event.widget.winfo_containing(event.x_root, event.y_root)
            if isinstance(widget_under_cursor, ttk.Combobox):
                return "break"
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        tree.bind('<MouseWheel>', scroll_treeview)
        canvas.bind('<MouseWheel>', scroll_treeview)

        def edit_cell(event):
            selected = tree.selection()
            if not selected:
                return
            item = selected[0]
            column = tree.identify_column(event.x)
            if column != '#6':
                return

            row_idx = int(item)
            row = self.transactions_df.iloc[row_idx]
            current_category = row['Категория']

            x, y, width, height = tree.bbox(item, column)
            combo = ttk.Combobox(edit_window, values=self.all_expense_categories, state='normal')
            combo.place(x=x, y=y, width=width, height=height)
            combo.set(current_category)

            def ignore_mouse_wheel(event):
                return "break"

            combo.bind('<MouseWheel>', ignore_mouse_wheel)

            def save_edit(event):
                new_category = combo.get().strip()
                if new_category and new_category != current_category:
                    self.transactions_df.at[row_idx, 'Категория'] = new_category
                    contractor = row['Контрагент']
                    description = row['Назначение платежа']
                    key = normalize_description(description)
                    OVERRIDE_CATEGORIES[key] = new_category
                    if new_category not in EXPENSE_CATEGORIES:
                        EXPENSE_CATEGORIES[new_category] = []
                        self.all_expense_categories = list(set(EXPENSE_CATEGORIES.keys()))
                    tree.item(item, values=(
                        row['Дата'], contractor, row['Сумма'], description, row['Тип'], new_category
                    ))
                combo.destroy()

            combo.bind('<Return>', save_edit)
            combo.bind('<FocusOut>', save_edit)
            combo.focus_set()

        tree.bind('<Double-1>', edit_cell)

        def save_and_close():
            for _, row in self.transactions_df.iterrows():
                if row["Категория"] == "Денежные средства":
                    continue
                current_date = row["Дата"]
                amount = row["Сумма"]
                category = row["Категория"]
                contractor = row["Контрагент"]
                description = str(row.get("Назначение платежа", "")).lower()
                channel = "cash" if any(keyword in description for keyword in EXPENSE_CATEGORIES['Денежные средства']) else "noncash"
                self.app.state.current_snapshot.expenses.append(
                    ExpenseRow(
                        date=current_date,
                        category=category,
                        contractor=contractor,
                        amount=amount,
                        channel=channel,
                        plan=0
                    )
                )
            logging.debug(f"Добавлено транзакций в current_snapshot.expenses: {len(self.app.state.current_snapshot.expenses)}")
            self.app.update_dashboard()
            self.app.update_tab_indicators()
            from expenses_tab import update_noncash_rows
            update_noncash_rows(self.app)
            self.app.owl_respond_command(f"Owl: Выписка загружена успешно. Период: {self.app.statement_period['start']}–{self.app.statement_period['end']}. Поступления наличных: {self.app.state.current_snapshot.cash.income:,.0f} руб.")
            response = self.check_expenses()
            self.app.owl_respond_command(f"Owl: {response}")
            cash_income = self.app.state.current_snapshot.cash.income
            cash_expenses = self.app.state.current_snapshot.cash.expenses
            cash_end = self.app.state.current_snapshot.cash.end
            if abs(cash_income - cash_expenses - cash_end) > 0.01:
                self.app.owl_respond_command(
                    f"Owl: Внимание! Кассовый остаток не сходится: Поступления ({cash_income:,.0f}) - Расходы ({cash_expenses:,.0f}) ≠ Остаток ({cash_end:,.0f})."
                )
            save_override_categories()
            edit_window.destroy()

        save_btn = tk.Button(edit_window, text="Сохранить и закрыть", command=save_and_close)
        save_btn.pack(pady=5)

    def check_revenue(self) -> str:
        if not self.app.state.current_snapshot.revenue:
            return "Данные о выручке не введены."
        
        anomalies = detect_anomalies(self.app.state.current_snapshot)
        total_revenue = sum(row.turnover_fact for row in self.app.state.current_snapshot.revenue)
        analysis = f"Проверка выручки. Общий оборот: {total_revenue:,.0f} руб.\n"
        analysis += "Аномалии:\n"
        if not anomalies:
            analysis += "Не найдено.\n"
        else:
            for anomaly in anomalies:
                if "рентабельность" in anomaly or "маржа" in anomaly:
                    analysis += f"- {anomaly}\n"
            if any("рентабельность" in anomaly for anomaly in anomalies):
                analysis += "Рекомендую уточнить данные по заказчикам.\n"
        return analysis

    def check_expenses(self) -> str:
        if not self.app.state.current_snapshot.expenses:
            return "Данные о расходах не введены."
        
        anomalies = detect_anomalies(self.app.state.current_snapshot)
        total_expenses = sum(item.amount for item in self.app.state.current_snapshot.expenses)
        analysis = f"Проверка расходов. Общая сумма: {total_expenses:,.0f} руб.\n"
        analysis += "Аномалии:\n"
        if not anomalies:
            analysis += "Не найдено.\n"
        else:
            for anomaly in anomalies:
                if "Неучтённые наличные" in anomaly or "отклонение от плана" in anomaly:
                    analysis += f"- {anomaly}\n"
            if anomalies:
                analysis += "Рассмотрите оптимизацию затрат.\n"
        return analysis

    def check_capital(self) -> str:
        anomalies = detect_anomalies(self.app.state.current_snapshot)
        total_assets = sum(item["fact"] for item in self.app.state.current_snapshot.balance.assets.bank_accounts.values()) + \
                       self.app.state.current_snapshot.cash.end + \
                       sum(row[1] for row in self.app.state.current_snapshot.balance.assets.debtors) + \
                       sum(row[4] for row in self.app.state.current_snapshot.balance.assets.equipment) + \
                       sum(row[1] for row in self.app.state.current_snapshot.balance.assets.inventory) + \
                       sum(row[1] for row in self.app.state.current_snapshot.balance.assets.vehicle) + \
                       sum(item["fact"] for item in self.app.state.current_snapshot.balance.assets.stocks.values())
        total_liabilities = sum(row[1] for row in self.app.state.current_snapshot.balance.liabilities.creditors if row[1] > 0) + \
                           self.app.state.current_snapshot.balance.liabilities.salary["fact"] + \
                           sum(item["fact"] for item in self.app.state.current_snapshot.balance.liabilities.taxes.values()) + \
                           sum(item["fact"] for item in self.app.state.current_snapshot.balance.liabilities.utilities.values()) + \
                           sum(item["fact"] for item in self.app.state.current_snapshot.balance.liabilities.rent.values()) + \
                           self.app.state.current_snapshot.balance.liabilities.accounting["fact"] + \
                           self.app.state.current_snapshot.balance.liabilities.other_contractors["fact"] + \
                           self.app.state.current_snapshot.balance.liabilities.credit_line["fact"] + \
                           self.app.state.current_snapshot.balance.liabilities.credit_card["fact"]
        capital = total_assets - total_liabilities
        analysis = (
            f"Проверка капитализации. Активы: {total_assets:,.0f}, Пассивы: {total_liabilities:,.0f}, "
            f"Капитализация: {capital:,.0f}.\n"
        )
        analysis += "Аномалии:\n"
        if not anomalies:
            analysis += "Не найдено.\n"
        else:
            for anomaly in anomalies:
                if "Δ капитализации" in anomaly or "Отрицательный склад" in anomaly or "Дебиторская оборачиваемость" in anomaly or "Высокая кредиторская задолженность" in anomaly:
                    analysis += f"- {anomaly}\n"
            if any("Высокая долговая нагрузка" in anomaly for anomaly in anomalies):
                analysis += "Высокая долговая нагрузка — сократите кредиты.\n"
        return analysis