import json
import logging
from typing import List, Dict, Any
from utils import (
    validate_month_format,
    validate_limit,
    filter_transactions_by_month,
    calculate_investment_for_transactions,
    prepare_investment_response
)

# Настройка основного логгера для services.py
logger = logging.getLogger(__name__)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> str:
    """
    Основная функция сервиса "Инвесткопилка".

    Args:
        month: Месяц для расчета в формате 'YYYY-MM'
        transactions: Список транзакций
        limit: Предел округления (10, 50, 100 и т.д.)

    Returns:
        JSON-строка с результатом расчета
    """
    logger.info(f"Запуск функции investment_bank для месяца: {month}, лимит: {limit}")

    # Валидация входных данных
    if not validate_month_format(month):
        logger.error(f"Неверный формат месяца: {month}")
        return json.dumps({
            "error": f"Неверный формат месяца: {month}. Ожидается 'YYYY-MM'",
            "status": "error"
        }, ensure_ascii=False)

    if not validate_limit(limit):
        logger.error(f"Неверный лимит: {limit}")
        return json.dumps({
            "error": f"Неверный лимит: {limit}. Лимит должен быть положительным и кратным 10",
            "status": "error"
        }, ensure_ascii=False)

    # Фильтрация транзакций по месяцу
    filtered_transactions = filter_transactions_by_month(transactions, month)

    if not filtered_transactions:
        logger.warning(f"Нет транзакций за указанный месяц: {month}")
        return prepare_investment_response(month, 0.0, limit)

    # Расчет суммы для инвесткопилки
    total_investment = calculate_investment_for_transactions(filtered_transactions, limit)

    logger.info(f"Расчет завершен. Сумма для копилки: {total_investment} ₽")

    # Подготовка ответа
    return prepare_investment_response(month, total_investment, limit)


def main_services_example():
    """
    Пример использования функции investment_bank
    """
    # Пример данных транзакций
    example_transactions = [
        {
            "Дата операции": "2024-01-15",
            "Сумма операции": -1712
        },
        {
            "Дата операции": "2024-01-20",
            "Сумма операции": -1245
        },
        {
            "Дата операции": "2024-02-01",
            "Сумма операции": -500
        }
    ]

    # Вызов основной функции
    result = investment_bank("2024-01", example_transactions, 50)

    print("Результат расчета Инвесткопилки:")
    print(result)

    return result
