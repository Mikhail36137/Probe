from dataclasses import dataclass
from typing import List, Dict, Any
import json
import os
from datetime import datetime

@dataclass
class CashData:
    start: float = 0.0
    income: float = 0.0
    expenses: float = 0.0
    end: float = 0.0

@dataclass
class RevenueRow:
    customer: str
    legal_entity: str
    turnover_fact: float
    beds_fact: float
    cost: float
    sebestoimost: float
    turnover_plan: float
    beds_plan: float
    cash_part: float
    noncash_part: float
    date: str

@dataclass
class ExpenseRow:
    date: str
    category: str
    contractor: str
    amount: float
    channel: str
    plan: float

@dataclass
class BalanceData:
    class Assets:
        def __init__(self):
            self.bank_accounts: Dict[str, Dict[str, float]] = {
                "ООО": {"fact": 0.0},
                "ИП": {"fact": 0.0}
            }
            self.debtors: List[List[Any]] = []
            self.equipment: List[List[Any]] = []
            self.inventory: List[List[Any]] = []
            self.vehicle: List[List[Any]] = []
            self.stocks: Dict[str, Dict[str, float]] = {
                "Баранова": {"fact": 0.0},
                "ДРБ": {"fact": 0.0},
                "ГДБ": {"fact": 0.0},
                "Буфеты на торговых точках": {"fact": 0.0},
                "Буфеты на складе сырья и в цехах": {"fact": 0.0}
            }

        def to_dict(self):
            return {
                "bank_accounts": self.bank_accounts,
                "debtors": self.debtors,
                "equipment": self.equipment,
                "inventory": self.inventory,
                "vehicle": self.vehicle,
                "stocks": self.stocks
            }

        @classmethod
        def from_dict(cls, data):
            assets = cls()
            assets.bank_accounts = data.get("bank_accounts", assets.bank_accounts)
            assets.debtors = data.get("debtors", assets.debtors)
            assets.equipment = data.get("equipment", assets.equipment)
            assets.inventory = data.get("inventory", assets.inventory)
            assets.vehicle = data.get("vehicle", assets.vehicle)
            assets.stocks = data.get("stocks", assets.stocks)
            return assets

    class Liabilities:
        def __init__(self):
            self.creditors: List[List[Any]] = []
            self.salary: Dict[str, float] = {"fact": 0.0}
            self.taxes: Dict[str, Dict[str, float]] = {
                "ЗП": {"fact": 0.0},
                "НДС": {"fact": 0.0},
                "Оборотный налог": {"fact": 0.0}
            }
            self.utilities: Dict[str, Dict[str, float]] = {
                "Баранова": {"fact": 0.0},
                "ДРБ": {"fact": 0.0},
                "ГДБ": {"fact": 0.0},
                "БСМП": {"fact": 0.0},
                "Буфеты": {"fact": 0.0}
            }
            self.rent: Dict[str, Dict[str, float]] = {
                "Баранова": {"fact": 0.0},
                "ДРБ": {"fact": 0.0},
                "ГДБ": {"fact": 0.0},
                "БСМП": {"fact": 0.0},
                "Буфеты": {"fact": 0.0}
            }
            self.accounting: Dict[str, float] = {"fact": 0.0}
            self.other_contractors: Dict[str, float] = {"fact": 0.0}
            self.credit_line: Dict[str, float] = {"fact": 0.0}
            self.credit_card: Dict[str, float] = {"fact": 0.0}

        def to_dict(self):
            return {
                "creditors": self.creditors,
                "salary": self.salary,
                "taxes": self.taxes,
                "utilities": self.utilities,
                "rent": self.rent,
                "accounting": self.accounting,
                "other_contractors": self.other_contractors,
                "credit_line": self.credit_line,
                "credit_card": self.credit_card
            }

        @classmethod
        def from_dict(cls, data):
            liabilities = cls()
            liabilities.creditors = data.get("creditors", liabilities.creditors)
            liabilities.salary = data.get("salary", liabilities.salary)
            liabilities.taxes = data.get("taxes", liabilities.taxes)
            liabilities.utilities = data.get("utilities", liabilities.utilities)
            liabilities.rent = data.get("rent", liabilities.rent)
            liabilities.accounting = data.get("accounting", liabilities.accounting)
            liabilities.other_contractors = data.get("other_contractors", liabilities.other_contractors)
            liabilities.credit_line = data.get("credit_line", liabilities.credit_line)
            liabilities.credit_card = data.get("credit_card", liabilities.credit_card)
            return liabilities

    def __init__(self):
        self.assets = self.Assets()
        self.liabilities = self.Liabilities()

    def to_dict(self):
        return {
            "assets": self.assets.to_dict(),
            "liabilities": self.liabilities.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        balance = cls()
        balance.assets = cls.Assets.from_dict(data.get("assets", {}))
        balance.liabilities = cls.Liabilities.from_dict(data.get("liabilities", {}))
        return balance

@dataclass
class PeriodSnapshot:
    revenue: List[RevenueRow]
    expenses: List[ExpenseRow]
    cash: CashData
    balance: BalanceData
    period_key: str = "2025-04-01_2025-04-30"

    def __init__(self):
        self.revenue = []
        self.expenses = []
        self.cash = CashData()
        self.balance = BalanceData()
        self.period_key = "2025-04-01_2025-04-30"

    def to_dict(self):
        return {
            "revenue": [r.__dict__ for r in self.revenue],
            "expenses": [e.__dict__ for e in self.expenses],
            "cash": self.cash.__dict__,
            "balance": self.balance.to_dict(),
            "period_key": self.period_key
        }

    def save_to_file(self, file_path: str):
        """Saves the period snapshot to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    @classmethod
    def from_dict(cls, data):
        snapshot = cls()
        snapshot.revenue = [RevenueRow(**r) for r in data.get("revenue", [])]
        snapshot.expenses = [ExpenseRow(**e) for e in data.get("expenses", [])]
        snapshot.cash = CashData(**data.get("cash", {}))
        snapshot.balance = BalanceData.from_dict(data.get("balance", {}))
        snapshot.period_key = data.get("period_key", "2025-04-01_2025-04-30")
        return snapshot

    @classmethod
    def load_from_file(cls, file_path: str):
        """Loads a period snapshot from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

class AppState:
    def __init__(self):
        self.current_snapshot = PeriodSnapshot()
        self.settings: Dict[str, Any] = {
            "expense_categories": [
                "Продукты", "Транспорт", "Коммунальные", "Развлечения", "Аренда", "Налоги",
                "Услуги_Медицинские", "Услуги_Юридические", "Услуги_Образовательные",
                "Услуги_Комиссии", "Услуги_Прочее", "Внутрифирменные", "Зарплата", "Прочее",
                "Денежные средства"
            ],
            "period": {
                "start_date": "2025-04-01",
                "end_date": "2025-04-30"
            },
            "suppliers": [],
            "customers": []
        }