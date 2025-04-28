import json
from unittest.mock import patch, Mock

import pytest
from requests_mock.contrib.fixture import Fixture

from src.views import collect_all_data


@pytest.fixture
def fake_data() -> dict:
    return {
        "greeting": "Добрый день!",
        "cards": [{"name": "Visa", "balance": 15000}],
        "top_transactions": [
            {"Дата операции": "2024-04-01", "Сумма операции": -1200, "Категория": "Еда", "Описание": "Продукты"}
        ],
        "currency_rates": {"USD": 91.1, "EUR": 97.3},
        "stock_prices": {"AAPL": 170.0, "GOOG": 2800.0},
    }


@patch("src.views.greetings")
@patch("src.views.cards")
@patch("src.views.top_transactions")
@patch("src.views.currency_rates")
@patch("src.views.stock_prices")
def test_collect_all_data_success(
    mock_stocks: Mock, mock_rates: Mock, mock_top: Mock, mock_cards: Mock, mock_greet: Mock, fake_data: Mock
) -> None:
    # Настройка моков
    mock_greet.return_value = fake_data["greeting"]
    mock_cards.return_value = fake_data["cards"]
    mock_top.return_value = fake_data["top_transactions"]
    mock_rates.return_value = fake_data["currency_rates"]
    mock_stocks.return_value = fake_data["stock_prices"]

    result_json = collect_all_data("2024-04-01")
    result = json.loads(result_json)

    assert result["greeting"] == fake_data["greeting"]
    assert result["cards"] == fake_data["cards"]
    assert result["currency_rates"] == fake_data["currency_rates"]
    assert isinstance(result["top_transactions"], list)
    assert "stock_prices" in result


@patch("src.views.greetings", side_effect=Exception("Something went wrong"))
def test_collect_all_data_error(mock_greetings: Mock) -> None:
    result_json = collect_all_data("2024-04-01")
    result = json.loads(result_json)
    assert "error" in result
    assert result["error"] == "Something went wrong"
