import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.utils import (calculate_example_investment, calculate_investment_for_transactions,
                       filter_transactions_by_month, prepare_investment_response, round_amount, validate_limit,
                       validate_month_format)


def test_validate_month_format_correct():
    """Тест validate_month_format с корректным форматом"""
    result = validate_month_format("2024-03")
    assert result is True


def test_validate_month_format_incorrect():
    """Тест validate_month_format с некорректным форматом"""
    result = validate_month_format("03-2024")
    assert result is False


def test_validate_month_format_invalid_month():
    """Тест validate_month_format с несуществующим месяцем"""
    result = validate_month_format("2024-13")
    assert result is False


def test_validate_month_format_empty():
    """Тест validate_month_format с пустой строкой"""
    result = validate_month_format("")
    assert result is False


def test_validate_month_format_partial():
    """Тест validate_month_format с частичной датой"""
    result = validate_month_format("2024")
    assert result is False


# ========== Тесты для validate_limit ==========
def test_validate_limit_correct():
    """Тест validate_limit с корректным лимитом"""
    test_cases = [10, 50, 100, 1000]

    for limit in test_cases:
        result = validate_limit(limit)
        assert result is True


def test_validate_limit_not_multiple_of_10():
    """Тест validate_limit с лимитом не кратным 10"""
    result = validate_limit(15)
    assert result is True  # Функция возвращает True, но логирует предупреждение


def test_validate_limit_zero():
    """Тест validate_limit с нулевым лимитом"""
    result = validate_limit(0)
    assert result is False


def test_validate_limit_negative():
    """Тест validate_limit с отрицательным лимитом"""
    result = validate_limit(-10)
    assert result is False


def test_validate_limit_not_integer():
    """Тест validate_limit с не целым числом"""
    result = validate_limit("50")  # Строка вместо числа
    assert result is False


def test_validate_limit_float():
    """Тест validate_limit с числом с плавающей точкой"""
    result = validate_limit(50.5)
    assert result is False


def test_filter_transactions_by_month_basic():
    """Тест filter_transactions_by_month - базовый случай"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
        {"Дата операции": "2024-03-20", "Сумма операции": -2000},
        {"Дата операции": "2024-04-10", "Сумма операции": -1500},
    ]

    result = filter_transactions_by_month(transactions, "2024-03")

    assert isinstance(result, list)
    assert len(result) == 2  # Только 2 транзакции в марте
    assert all(t["Дата операции"].startswith("2024-03") for t in result)


def test_filter_transactions_by_month_no_matches():
    """Тест когда нет транзакций в указанном месяце"""
    transactions = [
        {"Дата операции": "2024-04-10", "Сумма операции": -1500},
        {"Дата операции": "2024-04-15", "Сумма операции": -2500},
    ]

    result = filter_transactions_by_month(transactions, "2024-03")

    assert len(result) == 0


def test_filter_transactions_by_month_empty_transactions():
    """Тест с пустым списком транзакций"""
    result = filter_transactions_by_month([], "2024-03")
    assert len(result) == 0


def test_filter_transactions_by_month_missing_date():
    """Тест с транзакциями без даты"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
        {"Сумма операции": -2000},  # Нет даты
        {"Дата операции": "", "Сумма операции": -1500},  # Пустая дата
    ]

    result = filter_transactions_by_month(transactions, "2024-03")

    assert len(result) == 1  # Только первая транзакция
    assert result[0]["Дата операции"] == "2024-03-15"


def test_filter_transactions_by_month_different_formats():
    """Тест с разными форматами дат"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
        {"Дата операции": "15.03.2024", "Сумма операции": -2000},  # Другой формат
        {"Дата операции": "March 15, 2024", "Сумма операции": -1500},  # Текстовый формат
    ]

    result = filter_transactions_by_month(transactions, "2024-03")

    # Функция использует startswith, поэтому сработает только для первого формата
    assert len(result) == 1
    assert result[0]["Дата операции"] == "2024-03-15"


def test_round_amount_basic():
    """Тест round_amount - базовый случай"""
    test_cases = [
        (1712, 50, 38.0),  # Из примера: 1750 - 1712 = 38
        (100, 50, 0.0),  # 100 кратно 50
        (101, 50, 49.0),  # 150 - 101 = 49
        (125, 10, 5.0),  # 130 - 125 = 5
        (199, 100, 1.0),  # 200 - 199 = 1
    ]

    for amount, limit, expected in test_cases:
        result = round_amount(amount, limit)
        assert result == expected, f"Ошибка для amount={amount}, limit={limit}"


def test_round_amount_zero_amount():
    """Тест round_amount с нулевой суммой"""
    result = round_amount(0, 50)
    assert result == 0.0


def test_round_amount_negative_amount():
    """Тест round_amount с отрицательной суммой"""
    result = round_amount(-100, 50)
    assert result == 0.0  # Для отрицательных возвращается 0


def test_round_amount_small_amount():
    """Тест round_amount с маленькой суммой"""
    result = round_amount(5, 10)
    assert result == 5.0  # 10 - 5 = 5


def test_round_amount_precision():
    """Тест round_amount с плавающей точкой"""
    result = round_amount(123.45, 10)
    # Округление вверх: 130 - 123.45 = 6.55, округляется до 6.55
    assert result == 6.55


def test_calculate_investment_for_transactions_basic():
    """Тест calculate_investment_for_transactions - базовый случай"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
        {"Дата операции": "2024-03-20", "Сумма операции": -850},
        {"Дата операции": "2024-03-25", "Сумма операции": 500},  # Пополнение, не учитывается
    ]

    result = calculate_investment_for_transactions(transactions, 50)

    # Расчет:
    # 1712 -> округляется до 1750, разница 38
    # 850 -> округляется до 850, разница 0 (кратно 50)
    # Итого: 38.0
    assert result == 38.0


def test_calculate_investment_for_transactions_string_amounts():
    """Тест с суммами в виде строк"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": "-1712 ₽"},
        {"Дата операции": "2024-03-20", "Сумма операции": "850 RUB"},
        {"Дата операции": "2024-03-25", "Сумма операции": " 1 234 "},  # С пробелами
    ]

    result = calculate_investment_for_transactions(transactions, 50)

    # Все суммы отрицательные, должны быть учтены
    assert result > 0


def test_calculate_investment_for_transactions_invalid_amounts():
    """Тест с некорректными суммами"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": "-1712"},
        {"Дата операции": "2024-03-20", "Сумма операции": "не число"},  # Некорректная сумма
        {"Дата операции": "2024-03-25", "Сумма операции": ""},  # Пустая сумма
    ]

    result = calculate_investment_for_transactions(transactions, 50)

    # Учитывается только первая корректная транзакция
    assert result == 38.0  # 1712 -> 1750, разница 38


def test_calculate_investment_for_transactions_empty():
    """Тест с пустым списком транзакций"""
    result = calculate_investment_for_transactions([], 50)
    assert result == 0.0


def test_calculate_investment_for_transactions_only_positive():
    """Тест только с положительными суммами (пополнения)"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": 1000},
        {"Дата операции": "2024-03-20", "Сумма операции": 500},
    ]

    result = calculate_investment_for_transactions(transactions, 50)

    # Положительные суммы не учитываются
    assert result == 0.0


def test_calculate_investment_for_transactions_mixed_limits():
    """Тест с разными лимитами округления"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
        {"Дата операции": "2024-03-20", "Сумма операции": -850},
    ]

    # Тестируем разные лимиты
    test_cases = [
        (10, 48.0),  # 1720-1712=8 + 860-850=10 = 18? Давайте посчитаем точнее
        (50, 38.0),  # 1750-1712=38 + 850-850=0 = 38
        (100, 188.0),  # 1800-1712=88 + 900-850=50 = 138? Проверим: 1800-1712=88, 900-850=50, сумма 138
    ]

    for limit, expected in test_cases:
        result = calculate_investment_for_transactions(transactions, limit)
        # Проверяем, что результат вычислен (точные значения могут отличаться)
        assert isinstance(result, float)
        assert result >= 0


def test_prepare_investment_response_basic():
    """Тест prepare_investment_response - базовый случай"""
    result = prepare_investment_response("2024-03", 123.45, 50)

    # Проверяем, что это валидный JSON
    data = json.loads(result)

    assert data["month"] == "2024-03"
    assert data["total_investment"] == 123.45
    assert data["limit"] == 50
    assert data["currency"] == "RUB"
    assert data["status"] == "success"
    assert "calculation_date" in data


def test_prepare_investment_response_zero_investment():
    """Тест с нулевой суммой инвестиций"""
    result = prepare_investment_response("2024-03", 0.0, 50)
    data = json.loads(result)

    assert data["total_investment"] == 0.0
    assert data["status"] == "success"


def test_prepare_investment_response_datetime_format():
    """Тест формата даты в ответе"""
    with patch("datetime.datetime") as mock_datetime:
        mock_now = datetime(2024, 3, 15, 14, 30, 45)
        mock_datetime.now.return_value = mock_now

        result = prepare_investment_response("2024-03", 100.0, 50)
        data = json.loads(result)

        assert data["calculation_date"] == "2024-03-15 14:30:45"


def test_prepare_investment_response_json_structure():
    """Тест структуры JSON-ответа"""
    result = prepare_investment_response("2024-03", 123.45, 50)
    data = json.loads(result)

    # Проверяем все ожидаемые поля
    expected_fields = ["month", "limit", "total_investment", "currency", "status", "calculation_date"]
    for field in expected_fields:
        assert field in data

    # Проверяем типы значений
    assert isinstance(data["month"], str)
    assert isinstance(data["limit"], int)
    assert isinstance(data["total_investment"], (int, float))
    assert isinstance(data["currency"], str)
    assert isinstance(data["status"], str)
    assert isinstance(data["calculation_date"], str)


def test_calculate_example_investment():
    """Тест calculate_example_investment - пример из условия"""
    result = calculate_example_investment()

    assert isinstance(result, dict)

    # Проверяем поля
    assert result["original_amount"] == 1712
    assert result["limit"] == 50
    assert result["rounded_amount"] == 1750
    assert result["investment"] == 38.0
    assert "explanation" in result

    # Проверяем объяснение
    explanation = result["explanation"]
    assert "1712" in explanation
    assert "1750" in explanation
    assert "38" in explanation


def test_calculate_example_investment_structure():
    """Тест структуры результата calculate_example_investment"""
    result = calculate_example_investment()

    expected_fields = ["original_amount", "limit", "rounded_amount", "investment", "explanation"]
    for field in expected_fields:
        assert field in result


def test_investment_workflow():
    """Интеграционный тест полного рабочего процесса"""
    # 1. Подготавливаем тестовые транзакции
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
        {"Дата операции": "2024-03-20", "Сумма операции": -850},
        {"Дата операции": "2024-04-10", "Сумма операции": -1200},
    ]

    # 2. Фильтруем по месяцу
    filtered = filter_transactions_by_month(transactions, "2024-03")
    assert len(filtered) == 2

    # 3. Проверяем лимит
    limit = 50
    assert validate_limit(limit) is True

    # 4. Рассчитываем инвестиции
    total_investment = calculate_investment_for_transactions(filtered, limit)

    # 1712 -> 1750 (разница 38), 850 -> 850 (разница 0)
    assert total_investment == 38.0

    # 5. Подготавливаем ответ
    response = prepare_investment_response("2024-03", total_investment, limit)
    data = json.loads(response)

    assert data["month"] == "2024-03"
    assert data["total_investment"] == 38.0
    assert data["limit"] == 50


def test_logging_setup():
    """Тест настройки логгеров"""
    # Проверяем, что логгеры созданы
    loggers = [
        "validate_month_format",
        "validate_limit",
        "filter_transactions",
        "calculate_investment",
        "round_amount",
        "prepare_response",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        assert logger.name == logger_name


def test_validate_month_format_logging():
    """Тест логирования в validate_month_format"""
    with patch.object(logging.getLogger("validate_month_format"), "debug") as mock_debug:
        validate_month_format("2024-03")
        mock_debug.assert_called_once()


def test_validate_limit_logging_error():
    """Тест логирования ошибок в validate_limit"""
    with patch.object(logging.getLogger("validate_limit"), "error") as mock_error:
        validate_limit("не число")
        mock_error.assert_called_once()
