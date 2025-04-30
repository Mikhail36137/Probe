from tkinter import ttk
from typing import Any, List, Tuple

def update_tab_indicators(app: Any) -> None:
    """Обновляет индикаторы вкладок, отображая предупреждения о несохранённых данных."""
    TAB_NAMES: List[Tuple[str, bool]] = [
        ("Dashboard", False),  # Dashboard не требует индикатора
        ("Выручка", _has_unsaved_revenue(app)),
        ("Расходы", _has_unsaved_expenses(app)),
        ("Капитализация", _has_unsaved_capital(app)),
        ("Кредиторская задолженность", _has_unsaved_creditors(app)),
        ("Дебиторская задолженность", _has_unsaved_debtors(app)),
        ("Учёт активов", _has_unsaved_equipment(app)),
        ("Owl", False)  # Owl не требует индикатора
    ]

    for tab_name, has_warning in TAB_NAMES:
        tab_id: int | None = None
        for i in range(app.tab_control.index("end")):
            current_text = app.tab_control.tab(i, "text")
            if current_text == tab_name or current_text.startswith(f"{tab_name} ⚠"):
                tab_id = i
                break
        if tab_id is not None:
            app.tab_control.tab(tab_id, text=f"{tab_name} ⚠" if has_warning else tab_name)

def _has_unsaved_revenue(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Выручка'."""
    return hasattr(app, "customer_rows_state") and any(not state["added"] for state in app.customer_rows_state)

def _has_unsaved_expenses(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Расходы'."""
    noncash_unsaved = hasattr(app, "noncash_rows_state") and any(not state["added"] for state in app.noncash_rows_state)
    cash_unsaved = hasattr(app, "cash_rows_state") and any(not state["added"] for state in app.cash_rows_state)
    balance_unsaved = hasattr(app, "cash_balance_indicator") and app.cash_balance_indicator.cget("background") == "red"
    return noncash_unsaved or cash_unsaved or balance_unsaved

def _has_unsaved_capital(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Капитализация'."""
    assets_unsaved = hasattr(app, "assets_rows") and any(not row["added"] for row in app.assets_rows)
    liabilities_unsaved = hasattr(app, "liabilities_rows") and any(not row["added"] for row in app.liabilities_rows)
    return assets_unsaved or liabilities_unsaved

def _has_unsaved_creditors(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Кредиторская задолженность'."""
    return hasattr(app, "creditors_state") and any(not state["added"] for state in app.creditors_state)

def _has_unsaved_debtors(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Дебиторская задолженность'."""
    return hasattr(app, "debtors_state") and any(not state["added"] for state in app.debtors_state)

def _has_unsaved_equipment(app: Any) -> bool:
    """Проверяет наличие несохранённых данных на вкладке 'Учёт активов'."""
    return hasattr(app, "equipment_state") and any(not state["added"] for state in app.equipment_state)