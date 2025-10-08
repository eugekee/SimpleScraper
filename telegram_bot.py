import requests
import logging
from datetime import datetime, timedelta
import json
import time
import pandas as pd
from utils import read_excel_data
from config import EXCEL_FILE
import os

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def get_updates(self, offset=None):
        url = f"{self.base_url}/getUpdates"
        params = {'timeout': 30}
        if offset:
            params['offset'] = offset

        try:
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            return response.json().get('result', [])
        except Exception as e:
            logger.error(f"Ошибка при получении обновлений: {e}")
            return []

    def send_message(self, chat_id, text, parse_mode='HTML'):
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False

    def get_latest_data(self):
        try:
            df = read_excel_data()
            if df.empty:
                return None

            latest = df.iloc[-1].to_dict()
            return latest

        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return None

    def get_filtered_data(self, days=1, limit=10):
        try:
            df = read_excel_data()
            if df.empty:
                return None

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

            filtered_df = filtered_df.sort_values('timestamp', ascending=False)
            filtered_df = filtered_df.head(limit)

            return filtered_df.to_dict('records')

        except Exception as e:
            logger.error(f"Ошибка при получении отфильтрованных данных: {e}")
            return None

    def get_stats(self):
        try:
            df = read_excel_data()
            if df.empty:
                return {'error': 'Нет данных'}

            numeric_df = df[pd.to_numeric(df['price'], errors='coerce').notna()]

            if numeric_df.empty:
                return {
                    'total_records': len(df),
                    'message': 'Нет числовых данных для анализа'
                }

            prices = pd.to_numeric(numeric_df['price'])

            stats = {
                'total_records': len(df),
                'numeric_records': len(numeric_df),
                'date_range': {
                    'start': df['timestamp'].min(),
                    'end': df['timestamp'].max()
                },
                'price_stats': {
                    'current': float(prices.iloc[-1]),
                    'average': float(prices.mean()),
                    'min': float(prices.min()),
                    'max': float(prices.max()),
                    'change_24h': float(prices.iloc[-1] - prices.iloc[-2]) if len(prices) > 1 else 0
                }
            }

            return stats

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {'error': str(e)}

    def format_data_message(self, data):
        if not data:
            return "ОШИБКА: Данные временно недоступны"

        price = data.get('price', 'N/A')
        change = data.get('change', 'N/A')
        change_percent = data.get('change_percent', 'N/A')
        timestamp = data.get('timestamp', 'N/A')
        source = data.get('source', 'N/A')

        message = f"""
АКЦИИ СБЕРБАНКА

Цена: {price} руб.
Изменение: {change} ({change_percent}%)
Время: {timestamp}
Источник: {source}
        """

        return message.strip()

    def format_stats_message(self, stats):
        if not stats or 'error' in stats:
            return "ОШИБКА: Статистика временно недоступна"

        price_stats = stats.get('price_stats', {})

        message = f"""
СТАТИСТИКА ДАННЫХ

Всего записей: {stats.get('total_records', 0)}
Текущая цена: {price_stats.get('current', 'N/A')} руб.
Средняя цена: {price_stats.get('average', 'N/A')} руб.
Максимальная цена: {price_stats.get('max', 'N/A')} руб.
Минимальная цена: {price_stats.get('min', 'N/A')} руб.
Изменение за 24ч: {price_stats.get('change_24h', 'N/A')} руб.

Период данных:
   Начало: {stats.get('date_range', {}).get('start', 'N/A')}
   Конец: {stats.get('date_range', {}).get('end', 'N/A')}
        """

        return message.strip()

    def format_history_message(self, data, days):
        if not data:
            return "ОШИБКА: Исторические данные недоступны"

        message = f"ИСТОРИЯ ЗА ПОСЛЕДНИЕ {days} ДНЕЙ\n\n"

        for i, item in enumerate(data[:5], 1):
            price = item.get('price', 'N/A')
            change = item.get('change', 'N/A')
            change_percent = item.get('change_percent', 'N/A')
            timestamp = item.get('timestamp', 'N/A')

            try:
                dt = pd.to_datetime(timestamp)
                time_str = dt.strftime('%d.%m %H:%M')
            except:
                time_str = str(timestamp)

            message += f"{i}. {time_str}: {price} руб. | {change} ({change_percent}%)\n"

        if len(data) > 5:
            message += f"\n... и еще {len(data) - 5} записей"

        return message

    def process_command(self, chat_id, command, text):
        try:
            if command == '/start':
                welcome_message = """
БОТ МОНИТОРИНГА АКЦИЙ СБЕРБАНКА

Доступные команды:
/current - Текущая цена акций
/stats - Статистика данных
/history - История за 7 дней
/history3 - История за 3 дня
/history1 - История за 1 день
/help - Справка по командам

Данные обновляются автоматически каждые 5 минут.
                """
                return self.send_message(chat_id, welcome_message.strip())

            elif command == '/help':
                help_message = """
СПРАВКА ПО КОМАНДАМ

/current - Показать текущую цену акций Сбербанка
/stats - Показать статистику по всем данным
/history - История цен за 7 дней
/history3 - История цен за 3 дня  
/history1 - История цен за 1 день
/help - Эта справка

Бот использует реальные данные с финансовых сайтов
                """
                return self.send_message(chat_id, help_message.strip())

            elif command == '/current':
                data = self.get_latest_data()
                message = self.format_data_message(data)
                return self.send_message(chat_id, message)

            elif command == '/stats':
                stats = self.get_stats()
                message = self.format_stats_message(stats)
                return self.send_message(chat_id, message)

            elif command == '/history':
                data = self.get_filtered_data(days=7, limit=20)
                message = self.format_history_message(data, 7)
                return self.send_message(chat_id, message)

            elif command == '/history3':
                data = self.get_filtered_data(days=3, limit=15)
                message = self.format_history_message(data, 3)
                return self.send_message(chat_id, message)

            elif command == '/history1':
                data = self.get_filtered_data(days=1, limit=10)
                message = self.format_history_message(data, 1)
                return self.send_message(chat_id, message)

            else:
                return self.send_message(chat_id, "НЕИЗВЕСТНАЯ КОМАНДА. Используйте /help для списка команд.")

        except Exception as e:
            logger.error(f"Ошибка при обработке команды: {e}")
            return self.send_message(chat_id, "ОШИБКА: Произошла ошибка при обработке команды.")

    def run(self):
        logger.info("Запуск Telegram бота...")
        last_update_id = None

        while True:
            try:
                updates = self.get_updates(last_update_id)

                for update in updates:
                    last_update_id = update['update_id'] + 1

                    if 'message' in update and 'text' in update['message']:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message['text']
                        if text.startswith('/'):
                            command = text.split()[0]
                            logger.info(f"Обработка команды {command} от пользователя {chat_id}")
                            self.process_command(chat_id, command, text)

                time.sleep(1)

            except Exception as e:
                logger.error(f"Ошибка в основном цикле бота: {e}")
                time.sleep(5)


def run_telegram_bot():
    from config import TELEGRAM_BOT_TOKEN

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("TELEGRAM_BOT_TOKEN не установлен в config.py")
        print("ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
        print("Получите токен у @BotFather в Telegram и добавьте его в config.py")
        return

    bot = TelegramBot(TELEGRAM_BOT_TOKEN)
    bot.run()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_telegram_bot()