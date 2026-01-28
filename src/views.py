import json
import os
from typing import Any, Dict

from utils_views import (get_card, get_currency, get_date_period, get_path_and_period, get_stocks, get_time,
                         get_top_transactions)

os.chdir("C:/Users/20vik/myproject/Course_project")


def main_views(date_time: str) -> Dict[str, Any]:
    """
    Функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ.
    """
    # Работа с данными
    time_period = get_date_period(date_time)
    sorted_df = get_path_and_period("../data/operations.xlsx", time_period)

    # Приветствие
    greeting = get_time()
    # Информация по карте
    cards = get_card(sorted_df)
    # Топ транзакций
    top_transactions = get_top_transactions(sorted_df, 5)
    # Курс валют
    currency = get_currency("../user_settings.json")
    # Стоимость акций
    stocks = get_stocks("../user_settings.json")
    data = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency,
        "stock_prices": stocks,
    }

    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return json_data
