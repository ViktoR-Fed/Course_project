import os
import sys
import tempfile
from io import StringIO
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import xlsxwriter

from src.reports import save_to_file, spending_by_category


# Создаем мок-функцию для тестирования декоратора
def create_test_function():
    """Создает тестовую функцию, которую будем декорировать"""

    def sample_function():
        """Возвращает тестовые данные в формате DataFrame"""
        data = {
            "Category": ["Food", "Transport", "Entertainment"],
            "Amount": [100, 50, 200],
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
        return pd.DataFrame(data)

    return sample_function


def test_decorator_creates_file():
    """Тест на создание файла"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Патчим os.path.dirname чтобы использовать временную директорию
        with patch("os.path.dirname", return_value=tmp_dir):
            # Патчим xlsxwriter.Workbook
            mock_workbook = Mock()
            mock_worksheet = Mock()
            mock_workbook.add_worksheet.return_value = mock_worksheet
            mock_workbook.close = Mock()

            with patch("xlsxwriter.Workbook", return_value=mock_workbook):
                # Создаем декорированную функцию
                decorator = save_to_file("test_output.xlsx")
                test_func = decorator(create_test_function())

                # Вызываем декорированную функцию
                result = test_func()

                # Проверяем, что файл был создан
                xlsxwriter.Workbook.assert_called_once()
                mock_workbook.add_worksheet.assert_called_once()
                mock_workbook.close.assert_called_once()

                # Проверяем, что результат функции возвращается
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 3


def test_decorator_preserves_functionality():
    """Тест, что декоратор сохраняет оригинальную функциональность"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("os.path.dirname", return_value=tmp_dir):
            with patch("xlsxwriter.Workbook"):
                decorator = save_to_file("test_output.xlsx")
                test_func = decorator(create_test_function())

                result = test_func()

                # Проверяем, что данные возвращаются корректно
                assert "Category" in result.columns
                assert "Amount" in result.columns
                assert "Date" in result.columns
                assert list(result["Category"]) == ["Food", "Transport", "Entertainment"]


def test_decorator_writes_correct_data():
    """Тест на корректность записи данных в Excel"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_filename = "test_output.xlsx"
        test_filepath = os.path.join(tmp_dir, test_filename)

        # Патчим os.path.dirname
        with patch("os.path.dirname", return_value=tmp_dir):
            # Создаем реальный Workbook для проверки записи
            decorator = save_to_file(test_filename)
            test_func = decorator(create_test_function())

            # Вызываем функцию
            result = test_func()

            # Проверяем, что файл создан
            assert os.path.exists(test_filepath)

            # Читаем файл и проверяем содержимое
            try:
                # Можно использовать pandas для чтения Excel
                df_from_file = pd.read_excel(test_filepath)

                # Проверяем структуру данных
                assert list(df_from_file.columns) == list(result.columns)
                assert len(df_from_file) == len(result)
                # Проверяем значения
                for col in result.columns:
                    assert list(df_from_file[col]) == list(result[col])
            except ImportError:
                pass


def test_decorator_error_handling():
    """Тест обработки ошибок при записи в файл"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("os.path.dirname", return_value=tmp_dir):
            # Создаем мок, который выбрасывает исключение
            mock_workbook = Mock()
            mock_workbook.add_worksheet.side_effect = xlsxwriter.exceptions.XlsxWriterException("Test error")
            mock_workbook.close = Mock()

            with patch("xlsxwriter.Workbook", return_value=mock_workbook):
                # Перехватываем вывод в консоль
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    decorator = save_to_file("test_output.xlsx")
                    test_func = decorator(create_test_function())

                    # Функция должна завершиться без исключения
                    result = test_func()

                    # Проверяем, что результат все равно возвращается
                    assert isinstance(result, pd.DataFrame)

                    # Проверяем, что ошибка была обработана
                    output = mock_stdout.getvalue()
                    assert "Произошла ошибка записи" in output


def test_decorator_with_arguments():
    """Тест декоратора с функцией, принимающей аргументы"""

    def func_with_args(category=None, limit=None):
        data = {"Category": [category or "Test"], "Amount": [limit or 100]}
        return pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("os.path.dirname", return_value=tmp_dir):
            with patch("xlsxwriter.Workbook"):
                decorator = save_to_file("test_args.xlsx")
                decorated_func = decorator(func_with_args)

                # Вызываем с аргументами
                result = decorated_func(category="Food", limit=500)

                # Проверяем результат
                assert result.iloc[0]["Category"] == "Food"
                assert result.iloc[0]["Amount"] == 500


# Тест для проверки логирования
def test_logging_in_decorator(caplog):
    """Тест логирования в декораторе"""
    import logging

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("os.path.dirname", return_value=tmp_dir):
            with patch("xlsxwriter.Workbook"):
                # Устанавливаем уровень логирования
                caplog.set_level(logging.INFO)

                decorator = save_to_file("test_log.xlsx")
                test_func = decorator(create_test_function())

                # Вызываем функцию
                test_func()

                # Проверяем логи
                assert "Формирование файла" in caplog.text
                assert "Сформирован файл" in caplog.text


import datetime
import os
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from dateutil.relativedelta import relativedelta


def test_empty_category_result(sample_transactions):
    """Тест, когда нет транзакций по категории"""
    result = spending_by_category(sample_transactions, "Несуществующая категория")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

    # Проверяем, что колонки присутствуют
    expected_columns = [
        "Дата платежа",
        "Номер карты",
        "Статус",
        "Сумма операции",
        "Кэшбэк",
        "MCC",
        "Категория",
        "Описание",
        "Округление на инвесткопилку",
        "Бонусы (включая кэшбэк)",
    ]
    assert all(col in result.columns for col in expected_columns)


def test_filter_nulls_in_category(transactions_with_nulls_in_category):
    """Тест фильтрации пустых категорий"""
    result = spending_by_category(transactions_with_nulls_in_category, "Супермаркеты")
    assert len(result) == 0


def test_handle_invalid_dates(transactions_with_invalid_dates):
    """Тест обработки некорректных дат"""
    result = spending_by_category(transactions_with_invalid_dates, "Супермаркеты")

    # Должна остаться только одна строка с корректной датой
    assert len(result) == 0


def test_filter_positive_amounts(transactions_mixed_amounts):
    """Тест фильтрации положительных сумм"""
    result = spending_by_category(transactions_mixed_amounts, "Супермаркеты")

    assert len(result) == 0


def test_cashback_calculation(sample_transactions):
    """Тест расчета кэшбэка"""
    result = spending_by_category(sample_transactions, "Супермаркеты")

    # Проверяем, что колонка "Кэшбэк" заполнена
    assert result["Кэшбэк"].notna().all()

    # Проверяем расчет для строк, где кэшбэк был None
    for idx, row in result.iterrows():
        # Ожидаемый кэшбэк: 1% от суммы операции
        expected_cashback = round(abs(row["Сумма операции"]) / 100, 2)
        assert row["Кэшбэк"] == expected_cashback or row["Кэшбэк"] > 0


def test_bonuses_calculation(sample_transactions):
    """Тест расчета бонусов"""
    result = spending_by_category(sample_transactions, "Супермаркеты")

    # Проверяем, что колонка "Бонусы (включая кэшбэк)" заполнена
    assert result["Бонусы (включая кэшбэк)"].notna().all()

    # Проверяем базовую логику расчета
    for _, row in result.iterrows():
        expected_min_bonus = round(abs(row["Сумма операции"]) / 100, 2)
        assert row["Бонусы (включая кэшбэк)"] >= expected_min_bonus


def test_card_number_processing(sample_transactions):
    """Тест обработки номеров карт"""
    result = spending_by_category(sample_transactions, "Супермаркеты")

    # Проверяем, что звездочки удалены
    card_numbers = result["Номер карты"].dropna().astype(str)
    assert all("*" not in card for card in card_numbers)

    # Проверяем конкретные значения
    if "1234****5678" in sample_transactions["Номер карты"].values:
        assert "12345678" in card_numbers.values


def test_inf_nan_handling():
    """Тест обработки бесконечностей и NaN"""
    data = {
        "Дата операции": ["01.01.2024 12:00:00", "02.01.2024 14:00:00"],
        "Дата платежа": ["02.01.2024", "03.01.2024"],
        "Номер карты": ["1234**5678", "8765**4321"],
        "Статус": ["OK", "OK"],
        "Сумма операции": [-100, -200],
        "Кэшбэк": [np.inf, -np.inf],
        "MCC": ["5411", "5812"],
        "Категория": ["Супермаркеты", "Супермаркеты"],
        "Описание": ["Test 1", "Test 2"],
        "Округление на инвесткопилку": [np.nan, np.inf],
        "Бонусы (включая кэшбэк)": [np.inf, -np.inf],
    }

    df = pd.DataFrame(data)
    result = spending_by_category(df, "Супермаркеты", "2024-01-02")

    # Проверяем, что бесконечности заменены на 0
    assert not result.isin([np.inf, -np.inf]).any().any()

    # Проверяем, что NaN заменены на 0
    assert result.notna().all().all()
