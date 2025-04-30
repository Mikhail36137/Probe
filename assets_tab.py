import tkinter as tk
from tkinter import ttk, messagebox
import locale
from components import create_row
from utils import update_status
from typing import Any, List, Dict

def build_assets(app: Any) -> None:
    """Создаёт вкладку для учёта активов."""
    locale.setlocale(locale.LC_ALL, '')
    frame = ttk.Frame(app.tab_assets, padding=15)
    frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#d9d9d9")
    style.configure("TLabel", background="#d9d9d9")
    style.configure("TLabelFrame", background="#d9d9d9")
    style.configure("TButton", background="#d9d9d9")

    app.assets_status_label = ttk.Label(frame, text="")
    app.assets_status_label.pack(side="bottom", pady=5)

    app.assets_frame = ttk.LabelFrame(frame, text="Учёт активов", padding=10)
    app.assets_frame.pack(fill="both", expand=True)
    app.assets_frame.grid_columnconfigure(0, weight=1)

    headers = ["Название актива", "Тип", "Стоимость, ₽"]
    header_frame = ttk.Frame(app.assets_frame)
    header_frame.grid(row=0, column=0, sticky="ew")
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1, uniform="asset")
        ttk.Label(header_frame, text=header).grid(row=0, column=i, sticky="ew", padx=5)

    app.assets_rows: List[List] = []
    app.assets_rows_state: List[Dict] = []

    for _ in range(5):
        add_assets_row(app)

    app.assets_button_frame = ttk.Frame(app.assets_frame)
    app.assets_button_frame.grid(row=1, column=0, sticky="ew", pady=5)
    app.assets_button_frame.grid_columnconfigure((0, 1), weight=1)
    ttk.Button(app.assets_button_frame, text="+ Добавить строку",
               command=lambda: add_assets_row(app)).grid(row=0, column=0, sticky="ew", padx=5)
    ttk.Button(app.assets_button_frame, text="Анализ",
               command=lambda: analyze_assets(app)).grid(row=0, column=1, sticky="ew", padx=5)

def add_assets_row(app: Any) -> None:
    """Добавляет строку для учёта активов."""
    asset_types = ["Оборудование", "Инвентарь", "Транспорт", "Акции"]
    columns = [
        {"type": "entry"},
        {"type": "combobox", "values": asset_types},
        {"type": "entry"}
    ]
    row_idx = len(app.assets_rows) + 1
    row = create_row(
        app.assets_frame,
        columns,
        lambda r: add_assets_data_row(app, r),
        lambda r: delete_assets_row(app, r),
        app.state.settings,
        row_idx=row_idx
    )
    app.assets_rows.append(row)
    app.assets_rows_state.append({"indicator": row[-1], "added": False, "used_in_calculation": False, "row": row})
    app.update_tab_indicators()

def add_assets_data_row(app: Any, row: List[Any]) -> None:
    """Добавляет данные об активе."""
    try:
        asset_name = row[0].get()
        if not asset_name:
            messagebox.showerror("Ошибка", "Введите название актива.")
            app.assets_status_label.config(text="Ошибка: название актива не указано")
            return
        asset_type = row[1].get()
        if not asset_type:
            messagebox.showerror("Ошибка", "Выберите тип актива.")
            app.assets_status_label.config(text="Ошибка: тип актива не выбран")
            return
        value = locale.atof(row[2].get() or '0')

        # Добавляем актив в соответствующую категорию
        if asset_type == "Оборудование":
            app.state.current_snapshot.balance.assets.equipment.append((asset_name, 0, 0, 0, value))
        elif asset_type == "Инвентарь":
            app.state.current_snapshot.balance.assets.inventory.append((asset_name, value))
        elif asset_type == "Транспорт":
            app.state.current_snapshot.balance.assets.vehicle.append((asset_name, value))
        elif asset_type == "Акции":
            app.state.current_snapshot.balance.assets.stocks[asset_name] = {"fact": value}

        for state in app.assets_rows_state:
            if state["row"] == row:
                state["added"] = True
                state["used_in_calculation"] = True
                state["indicator"].config(background="green")

        app.update_dashboard()
        app.update_tab_indicators()
        update_status(app, f"Добавлен актив: {asset_name} ({asset_type})")
        app.assets_status_label.config(text=f"Добавлен актив: {asset_name}")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числовое значение для стоимости.")
        app.assets_status_label.config(text="Ошибка: некорректная стоимость")

def delete_assets_row(app: Any, row: List[Any]) -> None:
    """Удаляет строку актива."""
    asset_name = row[0].get()
    asset_type = row[1].get()

    # Удаляем актив из соответствующей категории
    if asset_type == "Оборудование":
        app.state.current_snapshot.balance.assets.equipment = [
            a for a in app.state.current_snapshot.balance.assets.equipment if a[0] != asset_name
        ]
    elif asset_type == "Инвентарь":
        app.state.current_snapshot.balance.assets.inventory = [
            a for a in app.state.current_snapshot.balance.assets.inventory if a[0] != asset_name
        ]
    elif asset_type == "Транспорт":
        app.state.current_snapshot.balance.assets.vehicle = [
            a for a in app.state.current_snapshot.balance.assets.vehicle if a[0] != asset_name
        ]
    elif asset_type == "Акции":
        app.state.current_snapshot.balance.assets.stocks.pop(asset_name, None)

    index = app.assets_rows.index(row)
    app.assets_rows.pop(index)
    app.assets_rows_state.pop(index)

    # Перестраиваем таблицу
    for widget in app.assets_frame.winfo_children():
        widget.destroy()

    app.assets_rows.clear()
    app.assets_rows_state.clear()

    headers = ["Название актива", "Тип", "Стоимость, ₽"]
    header_frame = ttk.Frame(app.assets_frame)
    header_frame.grid(row=0, column=0, sticky="ew")
    for i, header in enumerate(headers):
        header_frame.grid_columnconfigure(i, weight=1, uniform="asset")
        ttk.Label(header_frame, text=header).grid(row=0, column=i, sticky="ew", padx=5)

    for idx in range(5):
        add_assets_row(app)

    app.assets_button_frame = ttk.Frame(app.assets_frame)
    app.assets_button_frame.grid(row=1, column=0, sticky="ew", pady=5)
    app.assets_button_frame.grid_columnconfigure((0, 1), weight=1)
    ttk.Button(app.assets_button_frame, text="+ Добавить строку",
               command=lambda: add_assets_row(app)).grid(row=0, column=0, sticky="ew", padx=5)
    ttk.Button(app.assets_button_frame, text="Анализ",
               command=lambda: analyze_assets(app)).grid(row=0, column=1, sticky="ew", padx=5)

    app.update_dashboard()
    app.update_tab_indicators()
    app.assets_status_label.config(text=f"Удалён актив: {asset_name}")

def analyze_assets(app: Any) -> None:
    """Запускает анализ активов через Owl."""
    app.owl_respond_command("проверь активы")
    update_status(app, "Запущен анализ активов")
    app.assets_status_label.config(text="Запущен анализ активов")