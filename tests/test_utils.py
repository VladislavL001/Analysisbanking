import logging
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pandas.testing as pdt
import pytest
import requests
import requests_mock

from src.utils import (
    cards,
    currency_rates,
    date_format_obj,
    greetings,
    load_transactions,
    sorted_date,
    stock_prices,
    top_transactions,
)


def test_date_format_obj_valid() -> None:
    input_date = "23.01.2020 15:44:22"
    result = datetime(2020, 1, 23, 15, 44, 22)
    assert date_format_obj(input_date) == result


def test_date_format_obj_error() -> None:
    input_date = "213.012.2020 15:244:222"
    with pytest.raises(ValueError, match="Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ:СС"):
        date_format_obj(input_date)


def test_greeting_valid() -> None:
    input_date_1 = "23.01.2020 2:44:22"
    input_date_2 = "23.01.2020 7:44:22"
    input_date_3 = "23.01.2020 15:44:22"
    input_date_4 = "23.01.2020 19:44:22"
    assert greetings(input_date_1) == "Доброй ночи"
    assert greetings(input_date_2) == "Доброе утро"
    assert greetings(input_date_3) == "Добрый день"
    assert greetings(input_date_4) == "Добрый вечер"


def test_greeting_error() -> None:
    input_date = "213.012.2020 15:244:222"
    with pytest.raises(ValueError, match="Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ:СС"):
        greetings(input_date)


@pytest.fixture
def mock_path() -> Any:
    """Фикстура для подмены пути к файлу"""
    with patch("os.path.abspath") as mock_abspath:
        mock_abspath.return_value = "test_data/operations.xlsx"
        yield mock_abspath


@patch("pandas.read_excel")
def test_load_transactions_success(mock_read_excel: Mock, mock_path: Mock) -> None:
    """Тест успешной загрузки данных"""
    mock_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    mock_read_excel.return_value = mock_df

    df = load_transactions()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.equals(mock_df)


@patch("pandas.read_excel", side_effect=FileNotFoundError)
def test_load_transactions_file_not_found(mock_read_excel: Mock, mock_path: Mock, caplog: Any) -> None:
    """Тест обработки отсутствия файла"""
    with pytest.raises(FileNotFoundError):
        load_transactions()

    assert "Файл с операциями не найден!" in caplog.text


@patch("pandas.read_excel", side_effect=Exception("Ошибка загрузки"))
def test_load_transactions_generic_error(mock_read_excel: Mock, mock_path: Mock, caplog: Any) -> None:
    """Тест обработки общей ошибки"""
    with pytest.raises(Exception, match="Ошибка загрузки"):
        load_transactions()

    assert "Ошибка при загрузке файла: Ошибка загрузки" in caplog.text


@pytest.fixture
def df_test() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Дата операции": ["05.12.2021", "10.12.2021", "20.12.2021", "31.12.2021"],
            "Номер карты": ["0001", "0001", "0002", "0003"],
            "Сумма операции": [-5000, 2000, -3000, -2000],
        }
    )


def test_sorted_date_valid(df_test: pd.DataFrame) -> None:
    """Тесты функции sorted_data на работу"""
    current_day = datetime(2021, 12, 31)
    result = sorted_date(current_day, df_test).reset_index(drop=True)
    expected = pd.DataFrame(
        {
            "Дата операции": [datetime(2021, 12, 5), datetime(2021, 12, 20), datetime(2021, 12, 31)],
            "Номер карты": ["0001", "0002", "0003"],
            "Сумма операции": [5000, 3000, 2000],
        }
    )

    pdt.assert_frame_equal(result, expected)


@pytest.fixture
def mock_df() -> pd.DataFrame:
    """Фикстура с тестовыми данными."""
    return pd.DataFrame(
        {
            "Дата операции": [datetime(2024, 3, 1), datetime(2024, 3, 5), datetime(2024, 3, 10)],
            "Номер карты": ["1234567890123456", "1234567890123456", "Translation"],
            "Сумма операции": [5000, 2000, 3000],  # Условно отрицательные суммы уже взяли по модулю
        }
    )


@patch("src.utils.load_transactions")
@patch("src.utils.date_format_obj", return_value=datetime(2024, 3, 10))
@patch("src.utils.sorted_date")
def test_cards(mock_sorted_date: Mock, mock_date_format: Mock, mock_load_transactions: Mock, mock_df: Mock) -> None:
    """Тест функции cards()."""
    mock_sorted_date.return_value = mock_df

    result = cards("10.03.2024 23:59:59")

    expected = [
        {"last_digits": "3456", "total_spent": 7000.0, "cashback": 70.0},  # 7000 * 1%
        {"last_digits": "Translation", "total_spent": 3000.0, "cashback": 0.0},  # "Translation" → кешбэк 0
    ]

    assert result == expected


@patch("src.utils.load_transactions", side_effect=Exception("Ошибка базы данных"))
def test_cards_exception(mock_load_transactions: Mock) -> None:
    """Тест обработки исключения — если load_transactions() выбрасывает ошибку, должен вернуться пустой список."""
    result = cards("10.03.2024 23:59:59")
    assert result == [], f"Ожидался пустой список, но получили {result}"


def test_top_transactions_valid() -> None:
    """Проверка работы функции top_transactions"""
    mock_df = pd.DataFrame(
        {
            "Дата операции": [
                datetime(2024, 3, 1),
                datetime(2024, 3, 5),
                datetime(2024, 3, 10),
                datetime(2024, 3, 15),
                datetime(2024, 3, 20),
                datetime(2024, 3, 25),
            ],
            "Сумма операции": [1000, 5000, 2000, 7000, 3000, 4000],
            "Категория": ["Еда", "Путешествия", "Развлечения", "Покупки", "Транспорт", "Здоровье"],
            "Описание": ["Обед", "Билеты", "Кино", "Одежда", "Такси", "Аптека"],
        }
    )

    expected_result = [
        {"Дата операции": "15.03.2024", "Сумма операции": 7000, "Категория": "Покупки", "Описание": "Одежда"},
        {"Дата операции": "05.03.2024", "Сумма операции": 5000, "Категория": "Путешествия", "Описание": "Билеты"},
        {"Дата операции": "25.03.2024", "Сумма операции": 4000, "Категория": "Здоровье", "Описание": "Аптека"},
        {"Дата операции": "20.03.2024", "Сумма операции": 3000, "Категория": "Транспорт", "Описание": "Такси"},
        {"Дата операции": "10.03.2024", "Сумма операции": 2000, "Категория": "Развлечения", "Описание": "Кино"},
    ]

    with patch("src.utils.load_transactions", return_value=mock_df), patch(
        "src.utils.sorted_date", return_value=mock_df
    ):
        result = top_transactions("25.03.2024 23:55:22")

    assert result == expected_result


def test_currency_rates_success() -> Any:
    mock_response = {"Valute": {"USD": {"Value": 92.5}, "EUR": {"Value": 101.3}}}

    with requests_mock.Mocker() as m:
        m.get("https://www.cbr-xml-daily.ru/daily_json.js", json=mock_response)
        result = currency_rates()

    expected = [
        {"currency": "USD", "rate": 92.5},
        {"currency": "EUR", "rate": 101.3},
    ]
    assert result == expected


def test_currency_rates_request_error(caplog: Any) -> None:
    with requests_mock.Mocker() as m, caplog.at_level(logging.ERROR):
        m.get("https://www.cbr-xml-daily.ru/daily_json.js", status_code=500)
        result = currency_rates()

    assert result == []
    assert "Ошибка запроса курсов валют" in caplog.text


def test_currency_rates_timeout_error(caplog: Any) -> None:
    with requests_mock.Mocker() as m, caplog.at_level(logging.ERROR):
        m.get("https://www.cbr-xml-daily.ru/daily_json.js", exc=requests.exceptions.Timeout)
        result = currency_rates()

    assert result == []
    assert "Ошибка запроса курсов валют" in caplog.text


@patch("requests.get")
def test_successful_data_retrieval(mock_get: Mock) -> None:
    """Тест функции stock_prices на работу"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "securities": {"data": [["GAZP", "Gazprom", "Some Info", 234.67]]}  # Цена акций Газпрома
    }
    mock_get.return_value = mock_response

    expected = {"GAZP": 234.67, "GMKN": 234.67, "LKOH": 234.67, "NLMK": 234.67, "SBER": 234.67}
    actual = stock_prices()
    assert actual == expected


@patch("requests.get")
def test_error_in_response(mock_get: Mock) -> None:
    """Тест функции stock_prices на обработку ошибок"""
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    expected: dict = {}
    actual = stock_prices()
    assert actual == expected
