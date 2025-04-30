import unittest
import pandas as pd
import os
import shutil
from datetime import datetime
from state import PeriodSnapshot, RevenueRow, ExpenseRow, CashData, BalanceData
from data_processing import filter_by_period, aggregate_data, save_snapshot, load_snapshot
from anomaly_engine import detect_anomalies

class TestPulseBoard(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.snapshot = PeriodSnapshot()
        self.snapshot.revenue = [
            RevenueRow(
                customer="РБ", legal_entity="ООО", turnover_fact=100000,
                beds_fact=100, cost=500, sebestoimost=350, turnover_plan=0,
                beds_plan=0, cash_part=0, noncash_part=0, date="2025-04-01"
            ),
            RevenueRow(
                customer="Буфет 1", legal_entity="ИП", turnover_fact=50000,
                beds_fact=0, cost=0, sebestoimost=0, turnover_plan=0,
                beds_plan=0, cash_part=30000, noncash_part=20000, date="2025-04-02"
            ),
        ]
        self.snapshot.expenses = [
            ExpenseRow(
                date="2025-04-01", category="Аренда помещения", contractor="ООО Аренда",
                amount=30000, channel="noncash", plan=0
            ),
            ExpenseRow(
                date="2025-04-03", category="Заработная плата", contractor="",
                amount=20000, channel="cash", plan=0
            ),
        ]
        self.snapshot.cash = CashData(start=10000, income=50000, expenses=20000, end=40000)
        self.snapshot.balance = BalanceData()
        self.snapshot.balance.assets.bank_accounts = {
            "ООО": {"fact": 50000}, "ИП": {"fact": 20000}
        }
        self.snapshot.balance.assets.debtors = [["РБ", 10000]]
        self.snapshot.balance.assets.stocks = {"Баранова": {"fact": 10000}}
        self.snapshot.balance.liabilities.creditors = [["ООО Аренда", 30000]]
        self.snapshot.balance.liabilities.salary = {"fact": 20000}
        self.snapshot.balance.liabilities.taxes = {
            "ЗП": {"fact": 2000}, "НДС": {"fact": 5000}, "Оборотный налог": {"fact": 3000}
        }
        self.snapshot.balance.liabilities.utilities = {"Баранова": {"fact": 1000}}
        self.snapshot.balance.liabilities.rent = {"Баранова": {"fact": 5000}}
        self.snapshot.period_key = "2025-04-01_2025-04-30"

        save_snapshot(self.snapshot, self.snapshot.period_key)

    def tearDown(self):
        """Clean up after tests."""
        periods_dir = "periods"
        if os.path.exists(periods_dir):
            for file_name in os.listdir(periods_dir):
                file_path = os.path.join(periods_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            try:
                os.rmdir(periods_dir)
            except OSError:
                pass

    def test_filter_by_period(self):
        """Tests filtering data by custom period."""
        period_dict = {"start_date": "2025-04-01", "end_date": "2025-04-02"}
        filtered_revenue = filter_by_period([r.__dict__ for r in self.snapshot.revenue], period_dict)
        self.assertEqual(len(filtered_revenue), 2)
        period_dict = {"start_date": "2025-04-04", "end_date": "2025-04-05"}
        filtered_revenue = filter_by_period([r.__dict__ for r in self.snapshot.revenue], period_dict)
        self.assertEqual(len(filtered_revenue), 0)

    def test_aggregate_data(self):
        """Tests data aggregation for custom period."""
        period_dict = {"start_date": "2025-04-01", "end_date": "2025-04-30"}
        filtered_revenue = filter_by_period([r.__dict__ for r in self.snapshot.revenue], period_dict)
        aggregated = aggregate_data(filtered_revenue)
        self.assertEqual(aggregated["revenue"], 150000)
        filtered_expenses = filter_by_period([e.__dict__ for e in self.snapshot.expenses], period_dict)
        aggregated_expenses = aggregate_data(filtered_expenses)
        self.assertEqual(aggregated_expenses["expenses"], 50000)

    def test_save_load_snapshot(self):
        """Tests saving and loading a period snapshot."""
        loaded_snapshot = load_snapshot(self.snapshot.period_key)
        self.assertEqual(loaded_snapshot.period_key, self.snapshot.period_key)
        self.assertEqual(len(loaded_snapshot.revenue), 2)
        self.assertEqual(loaded_snapshot.revenue[0].customer, "РБ")
        self.assertEqual(loaded_snapshot.cash.income, 50000)

    def test_anomaly_detection(self):
        """Tests anomaly detection."""
        anomalies = detect_anomalies(self.snapshot)
        self.assertFalse(any("рентабельность" in anomaly for anomaly in anomalies))
        self.assertFalse(any("Несоответствие кассового остатка" in anomaly for anomaly in anomalies))
        self.assertFalse(any("Дебиторская оборачиваемость" in anomaly for anomaly in anomalies))

if __name__ == "__main__":
    unittest.main()