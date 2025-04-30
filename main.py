import tkinter as tk
from base_ui import PulseBoardPro
from revenue_tab import build_revenue
from expenses_tab import build_expenses
from capital_tab import build_capital
from dashboard_tab import build_dashboard
from owl_tab import build_owl
from debtors_creditors_tab import build_creditors, build_debtors
from equipment_tab import build_equipment
from state import AppState
from owl_agent import OwlAgent
import matplotlib.pyplot as plt
import logging
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class App(PulseBoardPro):
    def __init__(self, root):
        super().__init__(root)
        self.root.title("PulseBoard Pro: Ultimate Edition")
        self.state = AppState()  # Инициализация state
        self.owl = OwlAgent()   # Инициализация OwlAgent
        self.owl.app = self     # Связываем OwlAgent с приложением
        self.last_dir = os.path.expanduser("~")
        self.statement_period = {"start": "23.03.2025", "end": "26.03.2025"}
        logging.info("Инициализация приложения...")

        # Строим интерфейс
        try:
            logging.debug("Создание вкладок...")
            self.build_ui(
                build_dashboard=build_dashboard,
                build_revenue=build_revenue,
                build_expenses=build_expenses,
                build_capital=build_capital,
                build_creditors=build_creditors,
                build_debtors=build_debtors,
                build_equipment=build_equipment,
                build_owl=build_owl
            )
            logging.info("Интерфейс успешно построен")
        except Exception as e:
            logging.error(f"Ошибка при построении интерфейса: {e}")
            raise

        # Загрузка настроек
        self.load_settings()
        self.update_tab_indicators()
        logging.info("Приложение инициализировано")

    def load_settings(self):
        """Загружает настройки из settings.json."""
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.last_dir = settings.get("last_dir", os.path.expanduser("~"))
                self.state.settings.update(settings.get("settings", {}))
            logging.info("Настройки загружены")
        except FileNotFoundError:
            logging.warning("Файл settings.json не найден, используются настройки по умолчанию")
        except Exception as e:
            logging.error(f"Ошибка при загрузке настроек: {e}")

    def save_settings(self):
        """Сохраняет настройки в settings.json."""
        settings = {
            "last_dir": self.last_dir,
            "settings": self.state.settings
        }
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            logging.info("Настройки сохранены")
        except Exception as e:
            logging.error(f"Ошибка при сохранении настроек: {e}")

    def update_tab_indicators(self):
        """Обновляет индикаторы вкладок."""
        from tab_indicators import update_tab_indicators
        try:
            update_tab_indicators(self)
            logging.debug("Индикаторы вкладок обновлены")
        except Exception as e:
            logging.error(f"Ошибка при обновлении индикаторов вкладок: {e}")

    def update_dashboard(self):
        """Обновляет вкладку Dashboard."""
        try:
            build_dashboard(self)
            logging.debug("Вкладка Dashboard обновлена")
        except Exception as e:
            logging.error(f"Ошибка при обновлении Dashboard: {e}")

    def show_chart(self, chart_type: str):
        """Отображает графики."""
        logging.debug(f"Отображение графика: {chart_type}")
        try:
            if chart_type == "revenue":
                fig, ax = plt.subplots()
                customers = [row.customer for row in self.state.current_snapshot.revenue]
                turnover_fact = [row.turnover_fact for row in self.state.current_snapshot.revenue]
                ax.bar(customers, turnover_fact, label="Выручка факт")
                ax.set_title("Выручка по заказчикам")
                ax.set_xlabel("Заказчики")
                ax.set_ylabel("Сумма, ₽")
                ax.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.show()
            elif chart_type == "expenses":
                fig, ax = plt.subplots()
                categories = {}
                for expense in self.state.current_snapshot.expenses:
                    categories[expense.category] = categories.get(expense.category, 0) + expense.amount
                ax.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
                ax.set_title("Структура расходов")
                plt.show()
        except Exception as e:
            logging.error(f"Ошибка при отображении графика: {e}")

    def open_settings(self, key: str):
        """Открывает окно настроек."""
        from settings_tab import open_settings
        try:
            open_settings(self, key)
            logging.debug(f"Открыто окно настроек для ключа: {key}")
        except Exception as e:
            logging.error(f"Ошибка при открытии настроек: {e}")

    def owl_respond_command(self, command: str):
        """Обрабатывает команды для Owl."""
        try:
            from owl_tab import owl_respond_command
            owl_respond_command(self, command)
            logging.debug(f"Команда Owl обработана: {command}")
        except Exception as e:
            logging.error(f"Ошибка при обработке команды Owl: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    logging.info("Окно закрыто. Завершение работы.")