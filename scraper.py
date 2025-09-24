from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SberStockScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            logger.error(f"Ошибка при настройке драйвера: {e}")
            raise

    def get_stock_data(self):
        try:
            logger.info("Открываем страницу: https://www.profinance.ru/stock/sber")
            self.driver.get("https://www.profinance.ru/stock/sber")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            page_source = self.driver.page_source
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            logger.info("HTML страницы сохранен в debug_page.html")

            soup = BeautifulSoup(page_source, 'html.parser')

            stock_data = self.parse_stock_data(soup)

            return stock_data

        except Exception as e:
            logger.error("Ошибка при получении данных: %s", str(e))
            return self.create_error_data("SCRAPER_ERROR")
        finally:
            self.close_driver()

    def parse_stock_data(self, soup):
        try:
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'price': None,
                'change': None,
                'change_percent': None,
                'high': 'N/A',
                'low': 'N/A',
                'volume': 'N/A'
            }
            price_selectors = [
                '.stock-price', '.price', '.current-price',
                '#price', '[data-price]', '.ticker-price',
                'h1', 'h2', 'h3'
            ]

            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    price_match = re.search(r'(\d+[.,]\d+)', text)
                    if price_match and self.is_valid_price(price_match.group(1)):
                        data['price'] = price_match.group(1).replace(',', '.')
                        change_data = self.find_change_nearby(element, soup)
                        if change_data:
                            data.update(change_data)
                        break
                if data['price']:
                    break
            if not data['price']:
                text_content = soup.get_text()
                data.update(self.search_in_text(text_content))
            for key in ['price', 'change', 'change_percent']:
                if data[key] is None:
                    data[key] = 'N/A'

            logger.info(f"Итоговые данные: {data}")
            return data

        except Exception as e:
            logger.error(f"Ошибка при парсинге данных: {e}")
            return self.create_error_data("PARSE_ERROR")

    def is_valid_price(self, price_str):
        try:
            price = float(price_str.replace(',', '.'))
            return 100 <= price <= 500
        except ValueError:
            return False

    def find_change_nearby(self, element, soup):
        result = {'change': None, 'change_percent': None}

        parent = element.parent
        for _ in range(3):
            if parent:
                text = parent.get_text()
                changes = self.extract_changes(text)
                if changes:
                    return changes
                parent = parent.parent

        siblings = element.find_next_siblings() + element.find_previous_siblings()
        for sibling in siblings[:5]:
            text = sibling.get_text()
            changes = self.extract_changes(text)
            if changes:
                return changes

        return result

    def extract_changes(self, text):
        result = {'change': None, 'change_percent': None}
        pattern = r'([+-]\d+[.,]\d+)\s*\(([+-]\d+[.,]\d+)%\)'
        match = re.search(pattern, text)
        if match:
            result['change'] = match.group(1).replace(',', '.')
            result['change_percent'] = match.group(2).replace(',', '.')

        return result

    def search_in_text(self, text_content):
        result = {'price': None, 'change': None, 'change_percent': None}
        patterns = [
            r'(\d+[.,]\d+)\s*([+-]\d+[.,]\d+)\s*\(([+-]\d+[.,]\d+)%\)',
            r'цена[^\d]*(\d+[.,]\d+)[^+-]*([+-]\d+[.,]\d+)[^%]*%?([+-]?\d+[.,]\d+)%',
            r'сбер[^0-9+-]*(\d+[.,]\d+)[^0-9+-]*([+-]\d+[.,]\d+)[^0-9%]*([+-]\d+[.,]\d+)%'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                price, change, percent = matches[0]
                if self.is_valid_price(price):
                    result['price'] = price.replace(',', '.')
                    result['change'] = change.replace(',', '.')
                    result['change_percent'] = percent.replace(',', '.')
                    break

        return result

    def create_error_data(self, error_type):
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': error_type,
            'change': error_type,
            'change_percent': error_type,
            'high': error_type,
            'low': error_type,
            'volume': error_type
        }

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Ошибка при закрытии драйвера: {e}")


def scrape_sber_stock():
    scraper = None
    try:
        scraper = SberStockScraper(headless=True)
        data = scraper.get_stock_data()
        return data
    except Exception as e:
        logger.error(f"Критическая ошибка при скрапинге: {e}")
        return None
    finally:
        if scraper:
            scraper.close_driver()


if __name__ == "__main__":
    data = scrape_sber_stock()
    print("Результат парсинга:")
    for key, value in data.items():
        print(f"{key}: {value}")