import json
import unittest
from unittest.mock import patch, Mock

import pandas as pd

from src.services import cashback_analytics


class TestCashbackAnalytics(unittest.TestCase):

    @patch("src.services.load_transactions")
    def test_successful_cashback_analytics(self, mock_load: Mock) -> None:
        data = pd.DataFrame(
            {
                "Дата операции": ["15.03.2024 12:00:00", "22.03.2024 08:30:00"],
                "Категория": ["Супермаркеты", "АЗС"],
                "Кэшбэк": [10.5, 5.25],
            }
        )
        mock_load.return_value = data

        result = cashback_analytics("2024", "3")
        parsed = json.loads(result)

        self.assertEqual(parsed["Супермаркеты"], 10.5)
        self.assertEqual(parsed["АЗС"], 5.25)

    @patch("src.services.load_transactions")
    def test_empty_filtered_data(self, mock_load: Mock) -> None:
        data = pd.DataFrame(
            {"Дата операции": ["15.02.2024 12:00:00"], "Категория": ["Супермаркеты"], "Кэшбэк": [10.5]}
        )
        mock_load.return_value = data

        result = cashback_analytics("2024", "3")
        parsed = json.loads(result)

        self.assertEqual(parsed, {})

    @patch("src.services.load_transactions")
    def test_invalid_date_format(self, mock_load: Mock) -> None:
        data = pd.DataFrame({"Дата операции": ["неверная дата"], "Категория": ["Супермаркеты"], "Кэшбэк": [10.5]})
        mock_load.return_value = data

        result = cashback_analytics("2024", "3")
        parsed = json.loads(result)

        self.assertEqual(parsed, {})

    @patch("src.services.load_transactions")
    def test_exception_handling(self, mock_load: Mock) -> None:
        mock_load.side_effect = Exception("Ошибка загрузки данных")

        result = cashback_analytics("2024", "3")
        parsed = json.loads(result)

        self.assertIn("error", parsed)
        self.assertEqual(parsed["error"], "Ошибка загрузки данных")
