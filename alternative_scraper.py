import requests
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

#
def get_sber_price_simple():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        url = "https://www.profinance.ru/stock/sber"

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            if response.status_code == 200:
                text_content = response.text
                with open("debug_simple.html", "w", encoding="utf-8") as f:
                    f.write(text_content)
                patterns = [

                    r'(\d{3}[.,]\d{2})\s*([+-]\d+[.,]\d{2})\s*\(([+-]\d+[.,]\d+)%\)',

                    r'<td[^>]*>\s*цена[^<]*</td>\s*<td[^>]*>(\d+[.,]\d+)',

                    r'<h[1-3][^>]*>.*?(\d+[.,]\d{2}).*?</h[1-3]>',

                    r'<div[^>]*class=[^>]*price[^>]*>.*?(\d+[.,]\d{2})',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        if len(matches[0]) == 3:
                            price, change, percent = matches[0]
                            return {
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'price': price.replace(',', '.'),
                                'change': change.replace(',', '.'),
                                'change_percent': percent.replace(',', '.'),
                                'high': 'N/A',
                                'low': 'N/A',
                                'volume': 'N/A',
                                'source': 'simple_scraper'
                            }
                        else:
                            price = matches[0]
                            if isinstance(price, tuple):
                                price = price[0]
                            return {
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'price': price.replace(',', '.'),
                                'change': 'N/A',
                                'change_percent': 'N/A',
                                'high': 'N/A',
                                'low': 'N/A',
                                'volume': 'N/A',
                                'source': 'simple_scraper'
                            }

                price_match = re.search(r'>\s*(\d{3}[.,]\d{2})\s*<', text_content)
                if price_match:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'price': price_match.group(1).replace(',', '.'),
                        'change': 'N/A',
                        'change_percent': 'N/A',
                        'high': 'N/A',
                        'low': 'N/A',
                        'volume': 'N/A',
                        'source': 'simple_scraper'
                    }

        except requests.RequestException as e:
            logger.warning(f"Ошибка запроса: {e}")

        return None

    except Exception as e:
        logger.error(f"Ошибка в простом скрапере: {e}")
        return None