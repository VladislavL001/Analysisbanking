import json
import logging

import pandas as pd

from src.utils import load_transactions

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def cashback_analytics(year: str, month: str) -> str:
    try:
        logging.info(f"Загрузка транзакций за {month}.{year}")
        df = load_transactions()

        logging.info("Преобразование столбца 'Дата операции'")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        df = df.dropna(subset=["Дата операции"])

        logging.info("Фильтрация по дате")
        data_filtered = df[(df["Дата операции"].dt.year == int(year)) & (df["Дата операции"].dt.month == int(month))]

        if data_filtered.empty:
            logging.warning("Нет транзакций за указанный период")
            return json.dumps({}, ensure_ascii=False, indent=4)

        logging.info("Группировка и подсчёт кешбэка по категориям")
        cashback_by_category = data_filtered.groupby("Категория")["Кэшбэк"].sum().round(2).to_dict()

        sorted_filtered_cashback = dict(
            sorted(((cat, cb) for cat, cb in cashback_by_category.items() if cb > 0), key=lambda x: x[1], reverse=True)
        )

        logging.info("Анализ завершён успешно")
        return json.dumps(sorted_filtered_cashback, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Произошла ошибка при анализе: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    print(cashback_analytics("2021", "11"))
