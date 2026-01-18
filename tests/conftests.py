import pytest
import pandas as pd
from utils_views import get_card

@pytest.fixture
def sample_dataframe():
    """Фикстура для создания тестового DataFrame"""
    data = {
        "Дата операции": pd.to_datetime(["2024-01-15", "2024-01-10", "2024-01-20"]),
        "Номер карты": ["**1234", "5678", "**1234"],
        "Сумма операции": [1000, 2000, 1500],
        "Сумма операции с округлением": [1000, 2000, 1500],
        "Категория": ["Еда", "Транспорт", "Развлечения"]
    }
    return pd.DataFrame(data)


def test_with_fixture(sample_dataframe):
    """Тест с использованием фикстуры"""
    result = get_card(sample_dataframe)
    assert len(result) == 2  # 2 уникальные карты