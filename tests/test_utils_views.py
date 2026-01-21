import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from src.utils_views import (get_card, get_currency, get_date_period, get_path_and_period, get_stocks, get_time,
                             get_top_transactions)


def test_get_date_period_basic():
    """Базовый тест - середина месяца"""
    result = get_date_period("2024-03-15 14:30:00")

    assert len(result) == 2
    assert result[1] == "15.03.2024 14:30:00"  # Переданная дата


def test_get_date_period_first_day():
    """Тест для первого дня месяца"""
    result = get_date_period("2024-03-01 10:00:00")

    assert result[1] == "01.03.2024 10:00:00"  # Переданная дата


def test_get_date_period_last_day():
    """Тест для последнего дня месяца"""
    result = get_date_period("2024-03-31 23:59:59")

    assert result[0] == "01.03.2024 23:59:59"  # Начало месяца
    assert result[1] == "31.03.2024 23:59:59"  # Переданная дата


def test_get_date_period_different_format():
    """Тест с другим форматом даты"""
    result = get_date_period("15/03/2024 14:30", "%d/%m/%Y %H:%M")

    assert result[0] == "01.03.2024 14:30:00"
    assert result[1] == "15.03.2024 14:30:00"


def test_get_date_period_february():
    """Тест для февраля (короткий месяц)"""
    result = get_date_period("2024-02-28 12:00:00")

    assert result[0] == "01.02.2024 12:00:00"
    assert result[1] == "28.02.2024 12:00:00"


def test_get_date_period_leap_year():
    """Тест для високосного года"""
    result = get_date_period("2024-02-29 15:30:00")

    assert result[0] == "01.02.2024 15:30:00"
    assert result[1] == "29.02.2024 15:30:00"


def test_get_date_period_end_of_year():
    """Тест для конца года"""
    result = get_date_period("2024-12-31 23:59:59")

    assert result[0] == "01.12.2024 23:59:59"
    assert result[1] == "31.12.2024 23:59:59"


def test_get_date_period_start_of_year():
    """Тест для начала года"""
    result = get_date_period("2024-01-01 00:00:00")

    assert result[0] == "01.01.2024 00:00:00"
    assert result[1] == "01.01.2024 00:00:00"


def test_get_date_period_returns_list():
    """Тест, что функция возвращает список"""
    result = get_date_period("2024-03-15 14:30:00")

    assert isinstance(result, list)
    assert len(result) == 2


def test_get_date_period_custom_format():
    """Тест с кастомным форматом"""
    result = get_date_period("March 15, 2024 14:30:00", "%B %d, %Y %H:%M:%S")

    assert result[0] == "01.03.2024 14:30:00"
    assert result[1] == "15.03.2024 14:30:00"


def test_get_date_period_invalid_date():
    """Тест с некорректной датой (должен упасть)"""
    with pytest.raises(ValueError):
        get_date_period("2024-13-45 25:61:99")


def test_get_date_period_empty_string():
    """Тест с пустой строкой (должен упасть)"""
    with pytest.raises(ValueError):
        get_date_period("")


def test_get_date_period_none():
    """Тест с None (должен упасть)"""
    with pytest.raises(TypeError):
        get_date_period(None)


def test_filter_and_sort():
    """Фильтрация и сортировка данных"""
    # Создаем тестовые данные
    test_df = pd.DataFrame(
        {
            "Дата операции": [
                "2024-03-25 14:00:00",  # В периоде
                "2024-04-01 09:00:00",  # Вне периода
                "2024-03-10 10:00:00",  # В периоде
            ],
            "Сумма": [300, 400, 100],
            "Категория": ["А", "Б", "В"],
        }
    )

    period = ["01.03.2024 00:00:00", "31.03.2024 23:59:59"]

    with patch("pandas.read_excel", return_value=test_df):
        result = get_path_and_period("test.xlsx", period)

        # Проверяем
        assert len(result) == 2  # Только 2 строки в марте
        assert result["Дата операции"].iloc[0] < result["Дата операции"].iloc[1]  # Отсортировано


def test_empty_result():
    """Нет данных в периоде"""
    test_df = pd.DataFrame({"Дата операции": ["2024-04-01 09:00:00"], "Сумма": [100]})

    period = ["01.03.2024 00:00:00", "31.03.2024 23:59:59"]

    with patch("pandas.read_excel", return_value=test_df):
        result = get_path_and_period("test.xlsx", period)
        assert len(result) == 0  # Пустой результат


def test_reads_correct_sheet():
    """Чтение правильного листа Excel"""
    with patch("pandas.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame({"Дата операции": []})

        get_path_and_period("file.xlsx", ["01.01.2024 00:00:00", "31.01.2024 23:59:59"])

        # Проверяем что read_excel вызван с правильным sheet_name
        mock_read.assert_called_once_with("file.xlsx", sheet_name="Отчет по операциям")


def test_1_get_card():
    """Тест get_card - исправленная версия"""
    df = pd.DataFrame(
        {
            "Номер карты": ["1234****5678"],
            "Сумма операции": [-1000],  # Отрицательная сумма операции
            "Кэшбэк": [10.0],  # Кэшбэк
            "Сумма операции с округлением": [1000],  # ПОЛОЖИТЕЛЬНАЯ сумма с округлением!
        }
    )

    result = get_card(df)

    print(f"Результат: {result}")  # Для отладки

    # Проверяем структуру результата
    assert isinstance(result, list)
    assert len(result) == 1

    card = result[0]
    assert "last_digits" in card
    assert "total_spent" in card
    assert "cashback" in card

    assert card["last_digits"] == "12345678"
    assert card["total_spent"] == 1000  # ПОЛОЖИТЕЛЬНОЕ значение
    assert card["cashback"] == 10.0  # 1% от 1000


def test_2_get_top_transactions():
    """Минимальный тест get_top_transactions"""
    df = pd.DataFrame(
        {
            "Дата платежа": ["01.03.2024"],
            "Описание": ["Покупка"],
            "Категория": ["Еда"],
            "Сумма операции с округлением": [-500],
        }
    )

    result = get_top_transactions(df, 1)

    assert result[0]["date"] == "01.03.2024"
    assert result[0]["amount"] == "-500"
    assert result[0]["category"] == "Еда"


def test_3_get_currency():
    """Минимальный тест get_currency"""
    # Мок файла
    json_data = '{"user_currencies": ["USD"]}'

    # Мок API ответа
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": 90.0}

    with patch("builtins.open", mock_open(read_data=json_data)):
        with patch("requests.get", return_value=mock_response):
            result = get_currency("currency.json")

            assert result[0]["currency"] == "USD"
            assert result[0]["rate"] == 90.0


def test_4_get_stocks():
    """Минимальный тест get_stocks"""
    # Мок файла
    json_data = '{"user_stocks": ["AAPL"]}'

    # Мок API ответа
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"c": 175.5}]}

    with patch("builtins.open", mock_open(read_data=json_data)):
        with patch("requests.get", return_value=mock_response):
            with patch("datetime.date") as mock_date:
                mock_date.today.return_value = pd.Timestamp("2024-03-15").date()
                mock_date.side_effect = lambda *args, kwargs: pd.Timestamp(*args, kwargs).date()

                result = get_stocks("stocks.json")

                assert result[0]["stock"] == "AAPL"
                assert result[0]["price"] == 175.5
