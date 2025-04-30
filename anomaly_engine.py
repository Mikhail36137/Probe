from typing import List, Dict, Any
from state import PeriodSnapshot, RevenueRow
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_anomalies(current_snapshot: PeriodSnapshot, prev_snapshot: PeriodSnapshot = None, physical_cash: float = None) -> List[str]:
    """Обнаруживает аномалии в данных текущего периода, включая сверку физического остатка кассы."""
    anomalies = []
    logging.debug("Запуск обнаружения аномалий")

    # 1. Проверка маржи (< 15%) для выручки ООО
    for row in current_snapshot.revenue:
        if row.legal_entity == "ООО":
            margin = (row.turnover_fact - row.sebestoimost * row.beds_fact) / row.turnover_fact * 100 if row.turnover_fact > 0 else 0
            if margin < 15:
                anomalies.append(f"{row.customer}: рентабельность {margin:.2f}% ниже нормы (15%)")
                logging.info(f"Обнаружена низкая рентабельность для {row.customer}: {margin:.2f}%")

    # 2. Проверка кассового остатка
    cash_balance = current_snapshot.cash.start + current_snapshot.cash.income - current_snapshot.cash.expenses
    if abs(cash_balance - current_snapshot.cash.end) > 0.01:
        anomalies.append(f"Несоответствие кассового остатка: рассчитано {cash_balance:,.0f} руб, указано {current_snapshot.cash.end:,.0f} руб")
        logging.info(f"Обнаружено несоответствие кассового остатка: {cash_balance:,.0f} ≠ {current_snapshot.cash.end:,.0f}")

    # 3. Проверка физического остатка кассы
    if physical_cash is not None:
        if abs(current_snapshot.cash.end - physical_cash) > 0.01:
            anomalies.append(f"Расхождение с физическим остатком кассы: указано {current_snapshot.cash.end:,.0f} руб, физический остаток {physical_cash:,.0f} руб")
            logging.info(f"Обнаружено расхождение с физическим остатком кассы: {current_snapshot.cash.end:,.0f} ≠ {physical_cash:,.0f}")

    # 4. Проверка отрицательных складов
    for stock, value in current_snapshot.balance.assets.stocks.items():
        if value["fact"] < 0:
            anomalies.append(f"Отрицательный склад {stock}: {value['fact']:,.0f} руб")
            logging.info(f"Обнаружен отрицательный склад {stock}: {value['fact']:,.0f}")

    # 5. Проверка дебиторской оборачиваемости (> 45 дней)
    total_revenue = sum(row.turnover_fact for row in current_snapshot.revenue)
    debtors = sum(row[1] for row in current_snapshot.balance.assets.debtors)
    if total_revenue > 0:
        period_days = 30  # Условно, для месяца
        turnover_days = (debtors / total_revenue) * period_days
        if turnover_days > 45:
            anomalies.append(f"Дебиторская оборачиваемость: {turnover_days:.1f} дней (> 45 дней, риск ликвидности)")
            logging.info(f"Высокая дебиторская оборачиваемость: {turnover_days:.1f} дней")

    # 6. Проверка кредиторской задолженности относительно запасов
    creditors = sum(row[1] for row in current_snapshot.balance.liabilities.creditors if row[1] > 0)
    inventory = sum(row[1] for row in current_snapshot.balance.assets.inventory)
    stocks = sum(item["fact"] for item in current_snapshot.balance.assets.stocks.values())
    cogs_per_day = sum(row.sebestoimost * row.beds_fact / 30 for row in current_snapshot.revenue if row.legal_entity == "ООО")
    if (inventory + cogs_per_day * 30) > 0:
        creditors_to_inventory = creditors / (inventory + cogs_per_day * 30)
        if creditors_to_inventory > 1:
            anomalies.append(f"Высокая кредиторская задолженность: {creditors_to_inventory:.2f} относительно запасов (возможен кассовый разрыв)")
            logging.info(f"Высокая кредиторская задолженность: {creditors_to_inventory:.2f}")

    logging.debug(f"Обнаружено аномалий: {len(anomalies)}")
    return anomalies