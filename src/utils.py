import json
import datetime
import logging
from typing import Dict, List, Any


# Настройка логгеров для различных компонентов
validate_month_format_logger = logging.getLogger("validate_month_format")
validate_limit_logger = logging.getLogger("validate_limit")
filter_transactions_logger = logging.getLogger("filter_transactions")
calculate_investment_logger = logging.getLogger("calculate_investment")
round_amount_logger = logging.getLogger("round_amount")
prepare_response_logger = logging.getLogger("prepare_response")


def validate_month_format(month: str) -> bool:
    """
    Проверяет корректность формата месяца.

    Args:
        month: Строка в формате 'YYYY-MM'

    Returns:
        True если формат корректный, иначе False
    """
    try:
        datetime.datetime.strptime(month, '%Y-%m')
        validate_month_format_logger.debug(f"Месяц '{month}' прошел валидацию")
        return True
    except ValueError:
        validate_month_format_logger.error(f"Неверный формат месяца: {month}")
        return False


def validate_limit(limit: int) -> bool:
    """
    Проверяет корректность лимита округления.

    Args:
        limit: Целое число (10, 50, 100 и т.д.)

    Returns:
        True если лимит корректный, иначе False
    """
    if not isinstance(limit, int):
        validate_limit_logger.error(f"Лимит должен быть целым числом, получено: {type(limit)}")
        return False

    if limit <= 0:
        validate_limit_logger.error(f"Лимит должен быть положительным, получено: {limit}")
        return False

    if limit % 10 != 0:
        validate_limit_logger.warning(f"Лимит {limit} не кратен 10. Рекомендуется использовать 10, 50, 100")

    validate_limit_logger.debug(f"Лимит {limit} прошел валидацию")
    return True


def filter_transactions_by_month(
        transactions: List[Dict[str, Any]],
        target_month: str
) -> List[Dict[str, Any]]:
    """
    Фильтрует транзакции, оставляя только те, которые относятся к целевому месяцу.

    Args:
        transactions: Список транзакций
        target_month: Месяц в формате 'YYYY-MM'

    Returns:
        Отфильтрованный список транзакций
    """
    filtered = []

    for transaction in transactions:
        try:
            transaction_date = transaction.get("Дата операции", "")

            # Проверяем формат даты
            if not transaction_date:
                filter_transactions_logger.warning("Транзакция без даты пропущена")
                continue

            # Проверяем, относится ли транзакция к целевому месяцу
            if transaction_date.startswith(target_month):
                filtered.append(transaction)

        except Exception as e:
            filter_transactions_logger.error(f"Ошибка обработки транзакции: {e}")
            continue

    filter_transactions_logger.info(
        f"Отфильтровано {len(filtered)} из {len(transactions)} транзакций за {target_month}"
    )
    return filtered


def round_amount(amount: float, limit: int) -> float:
    """
    Округляет сумму до ближайшего кратного limit значения вверх.

    Args:
        amount: Сумма для округления (положительное число)
        limit: Шаг округления

    Returns:
        Разница между округленной и исходной суммой
    """
    if amount <= 0:
        return 0.0

    # Округляем вверх до ближайшего кратного limit
    rounded_up = ((amount + limit - 1) // limit) * limit
    difference = rounded_up - amount

    round_amount_logger.debug(f"Сумма: {amount}, округлено до: {rounded_up}, разница: {difference}")
    return round(difference, 2)


def calculate_investment_for_transactions(
        transactions: List[Dict[str, Any]],
        limit: int
) -> float:
    """
    Рассчитывает общую сумму для инвесткопилки из списка транзакций.Args:
        transactions: Список транзакций
        limit: Шаг округления

    Returns:
        Общая сумма для копилки
    """
    total = 0.0

    for i, transaction in enumerate(transactions):
        try:
            amount = transaction.get("Сумма операции", 0)

            # Преобразуем сумму к числу
            if isinstance(amount, str):
                # Очищаем строку от пробелов и символов валюты
                clean_amount = amount.replace(' ', '').replace('₽', '').replace('RUB', '')
                try:
                    amount_float = float(clean_amount)
                except ValueError:
                    calculate_investment_logger.warning(
                        f"Транзакция {i}: не удалось преобразовать сумму '{amount}'"
                    )
                    continue
            else:
                amount_float = float(amount)

            # Учитываем только расходы (отрицательные суммы)
            if amount_float < 0:
                investment = round_amount(abs(amount_float), limit)
                total += investment
                calculate_investment_logger.debug(
                    f"Транзакция {i}: расход {abs(amount_float)} ₽, "
                    f"в копилку: {investment} ₽"
                )

        except Exception as e:
            calculate_investment_logger.error(f"Ошибка в транзакции {i}: {e}")
            continue

    total = round(total, 2)
    calculate_investment_logger.info(f"Общая сумма для копилки: {total} ₽")
    return total


def prepare_investment_response(month: str, total_investment: float, limit: int) -> str:
    """
    Подготавливает JSON-ответ с результатами расчета.

    Args:
        month: Месяц расчета
        total_investment: Сумма в копилке
        limit: Использованный лимит округления

    Returns:
        JSON-строка с результатами
    """
    response_data = {
        "month": month,
        "limit": limit,
        "total_investment": total_investment,
        "currency": "RUB",
        "status": "success",
        "calculation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    prepare_response_logger.debug(f"Подготовлен ответ: {response_data}")

    return json.dumps(
        response_data,
        ensure_ascii=False,
        indent=2,
        default=str
    )


def calculate_example_investment() -> Dict[str, Any]:
    """
    Пример расчета из условия задачи.
    Демонстрирует работу алгоритма на примере.

    Returns:
        Словарь с результатами примера
    """
    example_transaction = {
        "Дата операции": "2024-01-15",
        "Сумма операции": -1712
    }

    limit = 50
    amount = abs(example_transaction["Сумма операции"])
    rounded_up = ((amount + limit - 1) // limit) * limit
    difference = rounded_up - amount

    return {
        "original_amount": amount,
        "limit": limit,
        "rounded_amount": rounded_up,
        "investment": difference,
        "explanation": f"Покупка на {amount} ₽ округляется до {rounded_up} ₽, "
                      f"в копилку уходит {difference} ₽"
    }