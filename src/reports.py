import json
import logging
from datetime import datetime
from typing import Optional, Any

import pandas as pd
from black.lines import Callable

from src.utils import load_transactions

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Декоратор
def report_to_file(filename: Optional[str] = None) -> Any:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            nonlocal filename
            if filename is None:
                filename = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    json.loads(result.to_json(orient="records", force_ascii=False)), f, indent=4, ensure_ascii=False
                )
            logging.info(f"Результат сохранён в {filename}")
            return result

        return wrapper

    return decorator


# Функция отчёта
@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    if date is None:
        end_date = datetime.now()
    else:
        end_date = pd.to_datetime(date, format="%d.%m.%Y")

    start_date = end_date - pd.DateOffset(months=3)

    transactions["Дата операции"] = pd.to_datetime(
        transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )
    filtered = transactions.dropna(subset=["Дата операции"])
    filtered = filtered[
        (filtered["Категория"] == category)
        & (filtered["Дата операции"] >= start_date)
        & (filtered["Дата операции"] <= end_date)
    ]
    return filtered[["Дата операции", "Категория", "Сумма операции"]].copy()


if __name__ in "__main":
    print(spending_by_category(load_transactions(), "Супермаркеты", "31.12.2021"))
