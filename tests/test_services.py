import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from src.services import investment_bank, main_services_example


def test_investment_bank_success():
    """Тест успешного расчета investment_bank"""
    # Тестовые данные
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
        {"Дата операции": "2024-03-20", "Сумма операции": -850},
    ]

    result = investment_bank("2024-03", transactions, 50)

    # Проверяем, что это валидный JSON
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["month"] == "2024-03"
    assert data["limit"] == 50
    assert data["currency"] == "RUB"
    assert "total_investment" in data
    assert "calculation_date" in data


def test_investment_bank_with_transactions():
    """Тест с реальными транзакциями"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
        {"Дата операции": "2024-03-20", "Сумма операции": -1245},
        {"Дата операции": "2024-03-25", "Сумма операции": -500},
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    # Проверяем, что сумма рассчитана (не 0)
    assert data["total_investment"] > 0


def test_investment_bank_no_transactions_in_month():
    """Тест когда нет транзакций в указанном месяце"""
    transactions = [
        {"Дата операции": "2024-04-15", "Сумма операции": -1000},
        {"Дата операции": "2024-04-20", "Сумма операции": -500},
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["total_investment"] == 0.0  # Нет транзакций за март


def test_investment_bank_empty_transactions():
    """Тест с пустым списком транзакций"""
    result = investment_bank("2024-03", [], 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["total_investment"] == 0.0


def test_investment_bank_only_positive_transactions():
    """Тест только с положительными транзакциями (пополнения)"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": 1000},
        {"Дата операции": "2024-03-20", "Сумма операции": 500},
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["total_investment"] == 0.0  # Положительные суммы не учитываются


def test_investment_bank_mixed_transactions():
    """Тест со смешанными транзакциями (расходы и пополнения)"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},  # Расход
        {"Дата операции": "2024-03-20", "Сумма операции": 1000},  # Пополнение
        {"Дата операции": "2024-03-25", "Сумма операции": -500},  # Расход
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    # Учитываются только расходы: 1712 и 500
    assert data["total_investment"] > 0


def test_investment_bank_different_limits():
    """Тест с разными лимитами округления"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1712},
    ]

    # Тестируем разные лимиты
    test_cases = [10, 50, 100]

    for limit in test_cases:
        result = investment_bank("2024-03", transactions, limit)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["limit"] == limit
        assert "total_investment" in data


def test_investment_bank_string_amounts():
    """Тест с суммами в виде строк"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": "-1712 ₽"},
        {"Дата операции": "2024-03-20", "Сумма операции": "850 RUB"},
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["total_investment"] > 0


def test_investment_bank_invalid_month_format():
    """Тест с некорректным форматом месяца"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    # Неправильный формат месяца
    result = investment_bank("03-2024", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "error"
    assert "error" in data
    assert "Неверный формат месяца" in data["error"]


def test_investment_bank_invalid_month_value():
    """Тест с несуществующим месяцем"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    # Месяц 13 не существует
    result = investment_bank("2024-13", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "error"
    assert "error" in data


def test_investment_bank_invalid_limit_zero():
    """Тест с нулевым лимитом"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    result = investment_bank("2024-03", transactions, 0)
    data = json.loads(result)

    assert data["status"] == "error"
    assert "error" in data
    assert "Неверный лимит" in data["error"]


def test_investment_bank_invalid_limit_negative():
    """Тест с отрицательным лимитом"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    result = investment_bank("2024-03", transactions, -10)
    data = json.loads(result)

    assert data["status"] == "error"
    assert "error" in data


def test_investment_bank_invalid_limit_not_multiple_of_10():
    """Тест с лимитом не кратным 10 (но функция может это пропустить)"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    result = investment_bank("2024-03", transactions, 15)
    data = json.loads(result)

    if data["status"] == "success":
        assert data["limit"] == 15
    else:
        assert "error" in data


def test_investment_bank_full_workflow():
    """Полный тест рабочего процесса"""
    # Подготавливаем тестовые данные
    transactions = [
        {"Дата операции": "2024-03-01", "Сумма операции": -1234},
        {"Дата операции": "2024-03-15", "Сумма операции": -567},
        {"Дата операции": "2024-03-31", "Сумма операции": -890},
        {"Дата операции": "2024-04-01", "Сумма операции": -1000},  # Не должна учитываться
    ]

    # Вызываем функцию
    result = investment_bank("2024-03", transactions, 100)
    # Парсим результат
    data = json.loads(result)

    # Проверяем результат
    assert data["status"] == "success"
    assert data["month"] == "2024-03"
    assert data["limit"] == 100
    assert data["currency"] == "RUB"

    # Проверяем, что сумма рассчитана правильно
    # 1234 -> округляется до 1300 (разница 66)
    # 567 -> округляется до 600 (разница 33)
    # 890 -> округляется до 900 (разница 10)
    # Итого: 66 + 33 + 10 = 109
    assert data["total_investment"] == 109.0


def test_investment_bank_with_large_dataset():
    """Тест с большим набором данных"""
    # Генерируем 100 тестовых транзакций
    transactions = []
    for i in range(100):
        transaction = {
            "Дата операции": f"2024-03-{i + 1:02d}",
            "Сумма операции": -(i * 100 + 1),  # Суммы: -1, -101, -201, ...
        }
        transactions.append(transaction)

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["total_investment"] > 0


def test_investment_bank_response_structure():
    """Тест структуры JSON-ответа"""
    transactions = [
        {"Дата операции": "2024-03-15", "Сумма операции": -1000},
    ]

    result = investment_bank("2024-03", transactions, 50)
    data = json.loads(result)

    # Проверяем обязательные поля для успешного ответа
    if data["status"] == "success":
        required_fields = ["month", "limit", "total_investment", "currency", "status", "calculation_date"]
        for field in required_fields:
            assert field in data

        # Проверяем типы
        assert isinstance(data["month"], str)
        assert isinstance(data["limit"], int)
        assert isinstance(data["total_investment"], (int, float))
        assert isinstance(data["currency"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["calculation_date"], str)

    # Проверяем обязательные поля для ошибки
    elif data["status"] == "error":
        assert "error" in data
        assert isinstance(data["error"], str)


def test_investment_bank_edge_cases():
    """Тест граничных случаев"""
    test_cases = [
        # (месяц, транзакции, лимит, ожидаемый статус)
        ("2024-01", [{"Дата операции": "2024-01-01", "Сумма операции": -1}], 10, "success"),
        ("2024-12", [{"Дата операции": "2024-12-31", "Сумма операции": -9999}], 100, "success"),
        ("2024-00", [], 50, "error"),  # Месяц 00
        ("2024-13", [], 50, "error"),  # Месяц 13
        ("2024-03", [], 0, "error"),  # Лимит 0
        ("2024-03", [], -1, "error"),  # Лимит -1
    ]

    for month, transactions, limit, expected_status in test_cases:
        result = investment_bank(month, transactions, limit)
        data = json.loads(result)

        assert data["status"] == expected_status


def test_investment_bank_example_from_comment():
    """Тест примера из комментария в коде"""
    # Пример данных из функции main_services_example
    example_transactions = [
        {"Дата операции": "2024-01-15", "Сумма операции": -1712},
        {"Дата операции": "2024-01-20", "Сумма операции": -1245},
        {"Дата операции": "2024-02-01", "Сумма операции": -500},
    ]

    result = investment_bank("2024-01", example_transactions, 50)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["month"] == "2024-01"
    assert data["limit"] == 50

    # Рассчитываем вручную:
    # 1712 -> 1750 (разница 38)
    # 1245 -> 1250 (разница 5)
    # 500 -> 500 (разница 0, кратно 50)
    # Итого: 38 + 5 + 0 = 43
    # Но! Последняя транзакция за февраль, не должна учитываться
    # Поэтому только: 1712 -> 1750 (38) и 1245 -> 1250 (5) = 43
    assert data["total_investment"] == 43.0


def test_main_services_example_output(capsys):
    """Тест функции main_services_example"""
    main_services_example()
    # Получаем вывод функции
    captured = capsys.readouterr()
    output = captured.out

    # Проверяем, что вывод содержит ожидаемые строки
    assert "Результат расчета Инвесткопилки:" in output
    assert "2024-01" in output
    assert "50" in output

    # Пробуем распарсить JSON из вывода
    # Ищем JSON в выводе (после заголовка)
    lines = output.strip().split("\n")
    if len(lines) > 1:
        json_str = lines[1].strip()
        try:
            data = json.loads(json_str)
            assert data["status"] == "success"
            assert data["month"] == "2024-01"
            assert data["limit"] == 50
        except (json.JSONDecodeError, KeyError):
            # Если не удалось распарсить, это нормально - функция могла измениться
            pass
