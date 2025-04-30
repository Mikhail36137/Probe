import tkinter as tk
from tkinter import ttk
from typing import Callable
from owl_agent import OwlAgent
from utils import update_status, log_message
from ui_theme import apply as apply_theme, toggle_dark  # Новые импорты темы

class PulseBoardPro:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("PulseBoard Pro: Умная Ревизия")
        self.root.geometry("1650x950")
        self.theme_mode: tk.StringVar = tk.StringVar(value="light")
        self.last_dir: str = ""
        self.settings: dict = {}
        try:
            self.root.iconphoto(True, tk.PhotoImage(file="icon.png"))
        except tk.TclError as e:
            log_message(f"Предупреждение: Не удалось загрузить иконку 'icon.png': {e}", level="WARNING")
        apply_theme(self.root)  # Применяем новую тему
        self.owl: OwlAgent = OwlAgent()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self) -> None:
        """Обрабатывает закрытие окна приложения."""
        update_status(self, "Окно закрыто. Завершение работы.")
        self.root.destroy()

    def update_theme(self) -> None:
        """Обновляет стили интерфейса при переключении темы."""
        toggle_dark(self)  # Используем функцию из ui_theme.py
        self.root.update()

    def build_ui(
        self,
        build_dashboard: Callable,
        build_revenue: Callable,
        build_expenses: Callable,
        build_capital: Callable,
        build_creditors: Callable,
        build_debtors: Callable,
        build_equipment: Callable,
        build_owl: Callable
    ) -> None:
        """Создаёт основной интерфейс приложения, добавляя вкладки."""
        main = ttk.Frame(self.root, style="Main.TFrame", padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="📊 PulseBoard Pro: Умная Ревизия", style="Title.TLabel").pack(anchor="w", pady=(0, 15))
        ttk.Checkbutton(main, text="Тёмная тема", variable=self.theme_mode, onvalue="dark", offvalue="light", command=self.update_theme).pack(anchor="ne")

        self.tab_control = ttk.Notebook(main)
        self.tab_dashboard = ttk.Frame(self.tab_control)
        self.tab_revenue = ttk.Frame(self.tab_control)
        self.tab_expenses = ttk.Frame(self.tab_control)
        self.tab_capital = ttk.Frame(self.tab_control)
        self.tab_creditors = ttk.Frame(self.tab_control)
        self.tab_debtors = ttk.Frame(self.tab_control)
        self.tab_equipment = ttk.Frame(self.tab_control)
        self.tab_owl = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_dashboard, text="Dashboard")
        self.tab_control.add(self.tab_revenue, text="Выручка")
        self.tab_control.add(self.tab_expenses, text="Расходы")
        self.tab_control.add(self.tab_capital, text="Капитализация")
        self.tab_control.add(self.tab_creditors, text="Кредиторская задолженность")
        self.tab_control.add(self.tab_debtors, text="Дебиторская задолженность")
        self.tab_control.add(self.tab_equipment, text="Учёт активов")
        self.tab_control.add(self.tab_owl, text="Owl")
        self.tab_control.pack(fill="both", expand=True)

        build_dashboard(self)
        build_revenue(self)
        build_expenses(self)
        build_capital(self)
        build_creditors(self)
        build_debtors(self)
        build_equipment(self)
        build_owl(self)

        self.status_frame = ttk.Frame(main)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_label = ttk.Label(self.status_frame, text="Статус: Готов к работе")
        self.status_label.pack(side="left", padx=5)