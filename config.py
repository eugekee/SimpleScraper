import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

SBER_URL = "https://www.profinance.ru/stock/sber"

WEBDRIVER_SETTINGS = {
    "headless": True,
    "timeout": 30
}

EXCEL_FILE = DATA_DIR / "sber_data.xlsx"
EXCEL_SHEET = "SBER_Prices"

MONITORING_INTERVAL = 300

MAX_MONITORING_DURATION = 24 * 60 * 60
SAVE_INTERVAL = 5

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8215328236:AAGH_iFNLselzOdXSo7aDkyWmpjHTCGAWQw')