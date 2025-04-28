import pandas as pd
import pytest
from pandas import DataFrame

from src.reports import spending_by_category


# Фикстура: создаем тестовый датафрейм
@pytest.fixture
def sample_transactions() -> DataFrame:
    data = {
        "Дата операции": [
            "01.03.2024 12:00:00",
            "15.04.2024 14:30:00",
            "20.01.2024 09:45:00",
            "10.02.2024 16:20:00",
            "05.04.2024 10:00:00",
        ],
        "Категория": ["Продукты", "Продукты", "Развлечения", "Продукты", "Транспорт"],
        "Сумма операции": [-1500.00, -1200.50, -800.00, -950.00, -300.00],
    }
    return pd.DataFrame(data)


# Тест 1: фильтрация по категории и дате
def test_spending_by_category_with_date(sample_transactions: DataFrame) -> None:
    result = spending_by_category(transactions=sample_transactions, category="Продукты", date="15.04.2024")

    assert not result.empty
    assert all(result["Категория"] == "Продукты")
    assert result["Дата операции"].max() <= pd.to_datetime("15.04.2024", format="%d.%m.%Y")
    assert result["Дата операции"].min() >= pd.to_datetime("15.01.2024", format="%d.%m.%Y")  # -3 месяца


# Тест 2: фильтрация без переданной даты (по текущей дате)
def test_spending_by_category_default_date(sample_transactions: DataFrame) -> None:
    result = spending_by_category(
        transactions=sample_transactions,
        category="Транспорт",
        date="15.04.2024",  # указываем дату, совпадающую с тестовыми данными
    )
    assert not result.empty
    assert all(result["Категория"] == "Транспорт")


# Тест 3: категория не найдена
def test_spending_by_category_no_matches(sample_transactions: DataFrame) -> None:
    result = spending_by_category(transactions=sample_transactions, category="Медицина", date="15.04.2024")

    assert result.empty
