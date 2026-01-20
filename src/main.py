import pandas as pd

from src.reports import file_path_param_r, spending_by_category
from src.services import main_services_example
from src.views import main_views

if __name__ == "__main__":
    print(main_views("2020-05-20 15:30:22"))
    transactions = pd.read_excel(file_path_param_r, sheet_name="Отчет по операциям")
    spending_by_category(transactions, "Аптеки", "2021-12-30 08:16:00")
    print(main_services_example())
