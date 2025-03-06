import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def date_format_obj(date_str: str) -> datetime:
    """Преобразует строку в объект datetime, если формат корректный."""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
    except ValueError:
        raise ValueError("Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ:СС")


def greetings(date_str: str) -> str:

    date_obj = date_format_obj(date_str)

    hour = date_obj.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 22:
        return "Добрый вечер"
    return "Доброй ночи"


def load_transactions() -> pd.DataFrame:
    """Загружает данные о транзакциях из Excel."""
    try:
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "operations.xlsx")
        )
        return pd.read_excel(path)
    except FileNotFoundError:
        logging.error("Файл с операциями не найден!")
        raise
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла: {e}")
        raise


def sorted_date(current_day: datetime, df: pd.DataFrame) -> pd.DataFrame:
    """Фильтрует и сортирует операции за текущий месяц."""
    df = df.copy()
    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"], errors="coerce", dayfirst=True
    )

    first_day_month = datetime(current_day.year, current_day.month, 1)
    df_filtered = df[
        (df["Дата операции"] >= first_day_month) & (df["Дата операции"] <= current_day)
    ]

    df_expenses = df_filtered[df_filtered["Сумма операции"] < 0].copy()
    df_expenses["Номер карты"] = df_expenses["Номер карты"].fillna("Translation")
    df_expenses["Сумма операции"] = df_expenses["Сумма операции"].abs()

    return df_expenses


def cards(date_str: str) -> list:
    """Возвращает список карт с суммами расходов и кешбэком."""
    try:
        df = load_transactions()
        current_day = date_format_obj(date_str)
        df_sorted = sorted_date(current_day, df)
    except Exception as e:
        logging.error(f"Ошибка при обработке карт: {e}")
        return []

    df_sum = (
        df_sorted.groupby("Номер карты", as_index=False)
        .agg(total_spent=("Сумма операции", "sum"))
        .round(2)
    )
    df_sum["cashback"] = (df_sum["total_spent"] / 100).round(2)
    df_sum.loc[df_sum["Номер карты"] == "Translation", "cashback"] = 0

    df_sum["last_digits"] = df_sum["Номер карты"].str[-4:]

    return df_sum[["last_digits", "total_spent", "cashback"]].to_dict("records")


def top_transactions(date_str: str) -> list:
    """Топ-5 транзакций по сумме."""
    try:
        df = load_transactions()
        current_day = date_format_obj(date_str)
        df_sorted = sorted_date(current_day, df)
    except Exception as e:
        logging.error(f"Ошибка при обработке транзакций: {e}")
        return []

    transactions_max = df_sorted.nlargest(5, "Сумма операции")[
        ["Дата операции", "Сумма операции", "Категория", "Описание"]
    ]
    transactions_max["Дата операции"] = transactions_max["Дата операции"].dt.strftime(
        "%d.%m.%Y"
    )

    return transactions_max.to_dict(orient="records")


def currency_rates() -> list:
    """Получает текущие курсы валют (USD, EUR) с сайта ЦБ РФ."""
    URL = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return [
            {"currency": "USD", "rate": data["Valute"]["USD"]["Value"]},
            {"currency": "EUR", "rate": data["Valute"]["EUR"]["Value"]},
        ]
    except requests.RequestException as e:
        logging.error(f"Ошибка запроса курсов валют: {e}")
        return []


def stock_prices() -> dict:
    """Получает текущие цены акций (Газпром, Сбербанк и др.)."""
    stocks_ticker = ["GAZP", "SBER", "NLMK", "GMKN", "LKOH"]
    stocks_dict = {}

    for stock in stocks_ticker:
        try:
            URL = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{stock}.json"
            response = requests.get(URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            stocks_dict[stock] = round(data["securities"]["data"][0][3], 2)
        except (requests.RequestException, IndexError, KeyError) as e:
            logging.error(f"Ошибка получения цены {stock}: {e}")

    return stocks_dict