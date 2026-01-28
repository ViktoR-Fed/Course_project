import json
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_STOCKS = os.getenv("API_KEY_STOCKS")
os.chdir("C:/Users/20vik/myproject/Course_project")

# Основная конфигурация logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    filename="../logs/views.log",
    encoding="utf-8",  # Запись логов в файл
    filemode="w",
)  # Перезапись файла при каждом запуске

# Создаем логеры для различных компонентов программы
get_time_logger = logging.getLogger("get_time")
get_date_period_logger = logging.getLogger("get_date_period")
get_path_and_period_logger = logging.getLogger("get_path_and_period")
get_card_logger = logging.getLogger("get_card")
get_top_transactions_logger = logging.getLogger("get_top_transactions")
get_currency_logger = logging.getLogger("get_currency")
get_stocks_logger = logging.getLogger("get_stocks")


# Работа с датой:
now = datetime.now()
# Сегодня
today = datetime.today().date()
# Вчера
yesterday = today - timedelta(days=1)


def get_time():
    """
    Функция, возвращающая «Доброе утро» / «Добрый день» / «Добрый вечер» /
    «Доброй ночи» в зависимости от текущего времени.
    """
    date_hour = datetime.now().hour
    if 5 <= date_hour < 12:
        return "Доброе утро"
    elif 12 <= date_hour < 18:
        return "Добрый день"
    elif 18 <= date_hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_date_period(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Функция для получения временного интервала начало месяца - сегодняшняя дата"""
    dt = datetime.strptime(date_time, date_format)
    start_month = dt.replace(day=1)
    return [start_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]


def get_path_and_period(path_file: str, period_date: list) -> DataFrame:
    """Функция принимает путь к xlsx-файлу и список дат, возвращает таблицу в заданном периоде."""
    df = pd.read_excel(path_file, sheet_name="Отчет по операциям")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
    last_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")

    filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= last_date)]
    sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)
    return sorted_df


def get_card(sorted_df: DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает список уникальных карт
    с суммарными показателями по операциям и кэшбэку
    """
    card_sorted = sorted_df[["Номер карты", "Сумма операции", "Кэшбэк", "Сумма операции с округлением"]]

    # Создаем словарь для агрегации данных по номерам карт
    card_dict = {}

    for index, row in card_sorted.iterrows():
        card_number = row["Номер карты"]
        last_digits = str(card_number).replace("*", "")

        # Получаем сумму операции с округлением (используем для расчета кэшбэка)
        total_spent = int(row["Сумма операции с округлением"])

        # Если карта уже встречалась, суммируем значения
        if card_number in card_dict:
            card_dict[card_number]["total_spent"] += total_spent
            # Кэшбэк пересчитываем заново от общей суммы
            card_dict[card_number]["cashback"] = card_dict[card_number]["total_spent"] / 100
        else:
            # Если карта новая, создаем запись
            card_dict[card_number] = {
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": total_spent / 100,
            }

    # Преобразуем словарь в список уникальных карт
    unique_cards = list(card_dict.values())

    return unique_cards


def get_top_transactions(sorted_df: DataFrame, get_top: int):
    """
    Функция принимает DataFrame и возвращает топ транзакций по сумме платежа
    """
    top_pay = []
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции с округлением", ascending=False)
    top_transactions = sorted_pay_df.head(get_top)
    top_transactions_sorted = top_transactions[
        ["Дата платежа", "Описание", "Категория", "Сумма операции с округлением"]
    ]
    for index, row in top_transactions_sorted.iterrows():
        transaction = {
            "date": f"{row["Дата платежа"]}",
            "amount": f"{row["Сумма операции с округлением"]}",
            "category": f"{row["Категория"]}",
            "description": f"{row["Описание"]}",
        }
        top_pay.append(transaction)
    return top_pay


def get_currency(pathfile: str) -> list[dict]:
    """
    Функция для получения курса валют
    """
    with open(pathfile, "r", encoding="utf-8") as file:
        data = json.load(file)
        currency = data["user_currencies"]
        currency_course = []
        for i in currency:
            url = f"https://api.apilayer.com/fixer/convert?to={"RUB"}&from={i}&amount={1}"
            payload = {}
            headers = {"apikey": API_KEY}
            response = requests.get(url, headers=headers, data=payload)
            result = round(response.json()["result"], 2)
            course = {"currency": i, "rate": result}
            currency_course.append(course)
    return currency_course


now = datetime.now()
today = datetime.today().date()
yesterday = today - timedelta(days=1)


def get_stocks(filepath: str) -> list[dict]:
    """
    Функция для получения стоимости акций
    """
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)
        user_stocks = data["user_stocks"]
        stocks_course = []
        for stock in user_stocks:
            url = (
                f"https://api.massive.com/v2/aggs/ticker/{stock}"
                f"/range/1/day/{yesterday}/{today}?adjusted=true&sort=asc&limit=120&apiKey={API_KEY_STOCKS}"
            )
            r = requests.get(url)
            data = r.json()
            result = data["results"]
            price = []
            for i in result:
                price.append(i)
            for i in price:
                price_stock = i["c"]
            course = {"stock": stock, "price": price_stock}
            stocks_course.append(course)
    return stocks_course
