import json
from src.utils import greetings, cards, top_transactions, currency_rates, stock_prices


def collect_all_data(date_str: str) -> str:
    """Собирает все данные в единый JSON-ответ."""
    try:
        result = {
            "greeting": greetings(date_str),
            "cards": cards(date_str),
            "top_transactions": [
                {
                    "date": t["Дата операции"],
                    "amount": t["Сумма операции"],
                    "category": t["Категория"],
                    "description": t["Описание"],
                }
                for t in top_transactions(date_str)
            ],
            "currency_rates": currency_rates(),
            "stock_prices": [
                {"stock": key, "price": value} for key, value in stock_prices().items()
            ],
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
