import json
import os
from datetime import datetime
from typing import Dict, List, Any
from utils import update_status
from state import PeriodSnapshot

settings_file: str = "settings.json"

def init_settings() -> Dict[str, any]:
    """Initializes the application settings, loading from file or using defaults."""
    default_settings: Dict[str, any] = {
        "last_dir": "",
        "customers": [
            "РБ", "РНД", "РПБ", "РИБ", "БСМП", "РКВД", "ДРБ", "ГДБ",
            "Баранова", "МЧС", "Буфет 1", "Буфет 2"
        ],
        "expense_categories": [
            "Продукты", "Транспорт", "Коммунальные", "Развлечения", "Аренда", "Налоги",
            "Услуги_Медицинские", "Услуги_Юридические", "Услуги_Образовательные",
            "Услуги_Комиссии", "Услуги_Прочее", "Внутрифирменные", "Зарплата", "Прочее",
            "Денежные средства"
        ],
        "suppliers": [],
        "equipment_types": [],
        "period": {"start_date": "2025-04-01", "end_date": "2025-04-30"}
    }
    settings = default_settings.copy()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения {settings_file}: {e}. Используются настройки по умолчанию.")
    try:
        save_settings(None, settings)
    except IOError as e:
        print(f"Ошибка записи {settings_file}: {e}")
    return settings

def save_settings(app, settings: Dict[str, any]) -> None:
    """Saves the application settings to settings.json."""
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except IOError as e:
        message = f"Ошибка сохранения настроек: {e}"
        print(message)
        if app:
            update_status(app, message)

def filter_by_period(data: List[Dict[str, Any]], period_dict: Dict[str, str]) -> List[Dict[str, Any]]:
    """Filters records by the specified date range."""
    start_date = period_dict["start_date"]
    end_date = period_dict["end_date"]
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print(f"Ошибка: Некорректный формат дат: {start_date} - {end_date}")
        return []

    filtered_data = []
    for item in data:
        item_date = item.get("date")
        if not item_date:
            continue
        try:
            item_dt = datetime.strptime(item_date, "%Y-%m-%d")
            if start_dt <= item_dt <= end_dt:
                filtered_data.append(item)
        except ValueError:
            print(f"Ошибка при парсинге даты записи: {item_date}. Запись: {item}")
            continue
    return filtered_data

def aggregate_data(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregates data for the specified period."""
    aggregated = {"revenue": 0.0, "expenses": 0.0}
    for item in data:
        if "turnover_fact" in item:
            aggregated["revenue"] += item["turnover_fact"]
        elif "amount" in item:
            aggregated["expenses"] += item["amount"]
    return aggregated

def save_snapshot(snapshot: PeriodSnapshot, period_key: str) -> None:
    """Saves the period snapshot to a file."""
    os.makedirs("periods", exist_ok=True)
    file_path = os.path.join("periods", f"{period_key}.json")
    snapshot.save_to_file(file_path)

def load_snapshot(period_key: str) -> PeriodSnapshot:
    """Loads a period snapshot from a file."""
    file_path = os.path.join("periods", f"{period_key}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Снимок периода {period_key} не найден.")
    return PeriodSnapshot.load_from_file(file_path)