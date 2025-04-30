from typing import Dict
from state import AppState, RevenueRow

def calculate_sebestoimost(customer: str, beds: float, capital_data: Dict[str, Dict]) -> float:
    """Рассчитывает себестоимость на основе заказчика и количества койко-дней."""
    if customer in ["Буфет 1", "Буфет 2"]:
        return 0
    stock_mapping = {
        "РБ": "Баранова", "РНД": "ДРБ", "РПБ": "ГДБ", "РИБ": "Баранова",
        "БСМП": "БСМП", "РКВД": "ДРБ", "ДРБ": "ДРБ", "ГДБ": "ГДБ",
        "Баранова": "Баранова", "МЧС": "Баранова"
    }
    stock_name = stock_mapping.get(customer, "Баранова")
    stock_value = capital_data["assets"]["stocks"].get(stock_name, {"fact": 0})["fact"]
    return stock_value / beds if beds > 0 else 0

def add_revenue(customer: str, turnover: float, beds: float, cost: float, state: AppState) -> RevenueRow:
    """Добавляет запись о выручке для заказчика (ООО)."""
    sebestoimost = calculate_sebestoimost(customer, beds, state.capital_data)
    revenue_row = RevenueRow(
        customer=customer,
        legal_entity="ООО",
        turnover_fact=turnover,
        beds_fact=beds,
        cost=cost,
        sebestoimost=sebestoimost,
        turnover_plan=0,
        beds_plan=0,
        cash_part=0,
        noncash_part=0
    )
    state.revenue_data[:] = [r for r in state.revenue_data if r.customer != customer]
    state.revenue_data.append(revenue_row)
    return revenue_row

def add_buffet_revenue(buffet: str, cash: float, noncash: float, sebestoimost: float, state: AppState) -> RevenueRow:
    """Добавляет запись о выручке для буфета (ИП)."""
    turnover = cash + noncash
    revenue_row = RevenueRow(
        customer=buffet,
        legal_entity="ИП",
        turnover_fact=turnover,
        beds_fact=0,
        cost=0,
        sebestoimost=sebestoimost,
        turnover_plan=0,
        beds_plan=0,
        cash_part=cash,
        noncash_part=noncash
    )
    state.revenue_data[:] = [r for r in state.revenue_data if r.customer != buffet]
    state.revenue_data.append(revenue_row)
    return revenue_row