import json
from src.services import  investment_bank


def test_investment_bank_success():
    """Тест успешного расчета"""
    transactions = [
        {"Дата операции": "2024-01-10", "Сумма операции": -1712},
        {"Дата операции": "2024-01-15", "Сумма операции": -245},
        {"Дата операции": "2024-02-01", "Сумма операции": -100}  # Не должен учитываться
    ]

    result = investment_bank("2024-01", transactions, 50)
    result_dict = json.loads(result)

    assert result_dict["status"] == "success"
    assert result_dict["month"] == "2024-01"
    assert result_dict["limit"] == 50
    assert "total_investment" in result_dict


def test_investment_bank_example_from_task():
    """Тест примера из условия задачи"""
    transactions = [
        {"Дата операции": "2024-01-15", "Сумма операции": -1712}
    ]

    result = investment_bank("2024-01", transactions, 50)
    result_dict = json.loads(result)

    # 1712 округляется до 1750, разница 38
    assert result_dict["total_investment"] == 38.0


def test_investment_bank_string_amounts():
    """Тест с суммами в виде строк"""
    transactions = [
        {"Дата операции": "2024-01-10", "Сумма операции": "-1712 ₽"},
        {"Дата операции": "2024-01-15", "Сумма операции": " -245.50 "},
        {"Дата операции": "2024-01-20", "Сумма операции": "500 RUB"}  # Пополнение, не учитывается
    ]

    result = investment_bank("2024-01", transactions, 10)
    result_dict = json.loads(result)

    assert result_dict["status"] == "success"


def test_investment_bank_empty_result():
    """Тест когда нет транзакций за указанный месяц"""
    transactions = [
        {"Дата операции": "2024-02-10", "Сумма операции": -100},
        {"Дата операции": "2024-02-15", "Сумма операции": -200}
    ]

    result = investment_bank("2024-01", transactions, 50)
    result_dict = json.loads(result)

    assert result_dict["total_investment"] == 0.0


def test_investment_bank_invalid_month():
    """Тест с неверным форматом месяца"""
    transactions = [{"Дата операции": "2024-01-10", "Сумма операции": -100}]

    result = investment_bank("2024/01", transactions, 50)
    result_dict = json.loads(result)

    assert result_dict["status"] == "error"


def test_investment_bank_invalid_limit():
    """Тест с неверным лимитом"""
    transactions = [{"Дата операции": "2024-01-10", "Сумма операции": -100}]

    result = investment_bank("2024-01", transactions, -10)
    result_dict = json.loads(result)

    assert result_dict["status"] == "error"


def test_investment_bank_mixed_transactions():
    """Тест со смешанными транзакциями (расходы и пополнения)"""
    transactions = [
        {"Дата операции": "2024-01-10", "Сумма операции": -1712},  # Учитывается
        {"Дата операции": "2024-01-11", "Сумма операции": 5000},  # Не учитывается (пополнение)
        {"Дата операции": "2024-01-12", "Сумма операции": -1245},  # Учитывается
        {"Дата операции": "2024-01-13", "Сумма операции": 0},  # Не учитывается
        {"Дата операции": "2024-01-14", "Сумма операции": -99}  # Учитывается
    ]

    result = investment_bank("2024-01", transactions, 100)
    result_dict = json.loads(result)

    # Проверяем что расчет произошел успешно
    assert result_dict["status"] == "success"
    assert isinstance(result_dict["total_investment"], float)
