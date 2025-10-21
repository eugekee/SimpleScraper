import time
import schedule
import sys
import os
from utils import monitor_sber_stock
from config import MONITORING_INTERVAL
import logging
#
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
is_monitoring = True


def run_monitoring():
    try:
        logger.info("Запуск мониторинга акций Сбербанка")
        result = monitor_sber_stock()

        if result and isinstance(result, dict):
            price = result.get('price', 'N/A')
            change = result.get('change', 'N/A')
            change_percent = result.get('change_percent', 'N/A')
            source = result.get('source', 'unknown')

            if price not in ['SCRAPE_ERROR', 'MONITOR_ERROR', 'PARSE_ERROR', 'SCRAPER_ERROR', 'NO_DATA', 'N/A']:
                logger.info("Мониторинг успешен. Цена: %s, Изменение: %s (%s), Источник: %s",
                            price, change, change_percent, source)
            else:
                logger.warning("Данные не найдены. Цена: %s, Источник: %s", price, source)
        else:
            logger.error("Мониторинг вернул некорректные данные")

        return result

    except Exception as e:
        logger.error("Ошибка в run_monitoring: %s", str(e))
        return None


def stop_monitoring():
    global is_monitoring
    is_monitoring = False
    logger.info("Остановка мониторинга...")


def continuous_monitoring_simple():
    global is_monitoring

    logger.info("Запуск непрерывного мониторинга")
    logger.info("Интервал: %s секунд", MONITORING_INTERVAL)
    logger.info("Для остановки нажмите Ctrl+C")

    iteration = 0

    try:
        while is_monitoring:
            iteration += 1
            logger.info("=== Итерация #%s ===", iteration)

            result = run_monitoring()
            wait_time = 0
            while wait_time < MONITORING_INTERVAL and is_monitoring:
                time.sleep(1)
                wait_time += 1

    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен по Ctrl+C")
    except Exception as e:
        logger.error("Ошибка в continuous_monitoring_simple: %s", str(e))
    finally:
        logger.info("Мониторинг завершен. Всего итераций: %s", iteration)


def single_monitoring():
    return run_monitoring()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Мониторинг акций Сбербанка')
    parser.add_argument('--continuous', '-c', action='store_true',
                        help='Непрерывный мониторинг')
    parser.add_argument('--single', '-s', action='store_true',
                        help='Однократный запуск')
    parser.add_argument('--interval', '-i', type=int,
                        help='Интервал мониторинга в секундах')
    parser.add_argument('--gui', '-g', action='store_true',
                        help='Запуск графического интерфейса')

    args = parser.parse_args()

    if args.gui:
        from flet_app import run_flet_app
        print("Запуск графического интерфейса...")
        run_flet_app()
        return

    global MONITORING_INTERVAL
    if args.interval:
        MONITORING_INTERVAL = args.interval

    if args.continuous:
        continuous_monitoring_simple()
    else:
        print("Запуск однократного мониторинга...")
        result = single_monitoring()
        if result:
            print("\nРезультаты:")
            for key, value in result.items():
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()