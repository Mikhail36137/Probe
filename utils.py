import logging
from typing import Any, Optional
from tkinter import ttk

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_status(app: Any, message: str) -> None:
    """Обновляет строку состояния в интерфейсе приложения."""
    try:
        if hasattr(app, "status_label") and isinstance(app.status_label, ttk.Label):
            app.status_label.config(text=f"Статус: {message}")
            log_message(message, level="INFO")
        else:
            log_message(f"Не удалось обновить статус: отсутствует status_label для сообщения '{message}'", level="WARNING")
    except Exception as e:
        log_message(f"Ошибка при обновлении статуса: {e}", level="ERROR")

def log_message(message: str, level: str = "INFO") -> None:
    """Логирует сообщение в консоль или файл."""
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)