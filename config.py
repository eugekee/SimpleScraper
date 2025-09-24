import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

SBER_URL = "https://www.profinance.ru/chart/sber"

WEBDRIVER_SETTINGS = {
    "headless": True,
    "timeout": 30
}

EXCEL_FILE = DATA_DIR / "sber_data.xlsx"
EXCEL_SHEET = "SBER_Prices"

MONITORING_INTERVAL = 300  # 5 минут

# Настройки мониторинга
MAX_MONITORING_DURATION = 24 * 60 * 60
SAVE_INTERVAL = 5