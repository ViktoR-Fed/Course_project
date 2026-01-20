import datetime
import logging
import os
from typing import Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import xlsxwriter  # type: ignore[import-untyped]
from dateutil.relativedelta import relativedelta

file_path_param_r = os.path.join(os.path.dirname(__file__), "../data/operations.xlsx")
logger = logging.getLogger("reports")
log = os.path.join(os.path.dirname(__file__), "..", "logs", "reports.log")
file_handler = logging.FileHandler(
    os.path.join(os.path.dirname(__file__), "../logs/reports.log"),
    "w",
    encoding="utf-8",
)
file_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def save_to_file(filename):  # type:ignore[no-untyped-def]
    """записывает в файл результат из spending_by_category"""

    def decorator(func):  # type:ignore[no-untyped-def]
        def wrapper(*args, **kwargs):  # type:ignore[no-untyped-def]
            resulted = func(*args, **kwargs)
            workbook = None

            try:
                logger.info("Формирование файла")
                workbook = xlsxwriter.Workbook(os.path.join(os.path.dirname(__file__), filename))
                worksheet = workbook.add_worksheet()
                for col_num, col_data in enumerate(resulted.columns):
                    worksheet.set_column(col_num, col_num, 50)

                # Запись заголовков
                for col_num, col_name in enumerate(resulted.columns):
                    worksheet.write(0, col_num, col_name)

                # Запись данных
                for row_num, row_data in enumerate(resulted.values):
                    worksheet.write_row(row_num + 1, 0, row_data)

                logger.info("Сформирован файл")

            except xlsxwriter.exceptions.XlsxWriterException as e:
                logger.error(f"Произошла ошибка {e}")
                print(f"Произошла ошибка записи {str(e)}")

            finally:
                workbook.close()

            return resulted

        return wrapper

    return decorator  # type: ignore[return-value]


@save_to_file(
    filename=os.path.join(os.path.dirname(__file__), "../data/result.xlsx")
)  # type: ignore[func-returns-value]
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает расходы по выбранной категории за 3 последних месяца от заданного/текущего"""
    from dateutil.relativedelta import relativedelta
    import datetime

    # Конвертируем дату операции
    transactions["Дата операции"] = pd.to_datetime(
        transactions["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
        errors='coerce'
    )

    # Удаляем строки с некорректными датами
    transactions = transactions.dropna(subset=["Дата операции"])

    logger.info("фильтрация дат и очистка категорий от пустых значений")

    # Удаляем пустые категории
    filtered_data = transactions.dropna(subset=["Категория"])

    logger.info("получение точки начала периода")

    if date:
        # Если указана дата, используем ее
        try:
            specific_date = pd.to_datetime(date).date()
        except:
            # Если не удалось распарсить дату, используем сегодня
            specific_date = datetime.datetime.today().date()
    else:
        # Если дата не указана, используем сегодня
        specific_date = datetime.datetime.today().date()

    # Вычисляем дату 3 месяца назад
    three_months_ago = specific_date - relativedelta(months=3)

    # Фильтруем по периоду (последние 3 месяца)
    filtered_data_start = filtered_data[
        (filtered_data["Дата операции"].dt.date >= three_months_ago) &
        (filtered_data["Дата операции"].dt.date <= specific_date)
        ]

    logger.info("подбор необходимых данных")

    # Фильтруем по категории и отрицательным суммам
    filter_result = filtered_data_start[
        (filtered_data_start["Сумма операции"] < 0) &
        (filtered_data_start["Категория"] == category)
        ].copy()

    # Выбираем нужные колонки
    resulted = filter_result[[
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
    ]].copy()

    # Обработка номеров карт
    resulted["Номер карты"] = resulted["Номер карты"].apply(
        lambda x: x.replace("*", "") if isinstance(x, str) else x
    )

    # Расчет кэшбэка (1% от суммы операции, если не указан)
    resulted["Кэшбэк"] = resulted["Кэшбэк"].fillna(
        round(abs(resulted["Сумма операции"]) / 100, 2)
    )

    # Расчет бонусов
    resulted["Бонусы (включая кэшбэк)"] = np.where(
        resulted["Бонусы (включая кэшбэк)"].isna(),
        round(abs(resulted["Сумма операции"]) / 100, 2),
        round(
            resulted["Бонусы (включая кэшбэк)"] + abs(resulted["Сумма операции"]) / 100,
            2,
        ),
    )

    # Замена бесконечностей и NaN на 0
    resulted = pd.DataFrame(resulted.replace([np.inf, -np.inf], np.nan).fillna(0))

    return resulted
