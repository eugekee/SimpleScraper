import time
import threading
import json
from datetime import datetime
import logging
from config import MAX_MONITORING_DURATION, MONITORING_INTERVAL
#
logger = logging.getLogger(__name__)


class MonitoringManager:
    def __init__(self):
        self.start_time = None
        self.is_monitoring = False
        self.auto_stop_timer = None
        self.monitoring_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_success': None,
            'last_error': None
        }

    def start_monitoring(self, max_duration=None):
        try:
            if max_duration is None:
                max_duration = MAX_MONITORING_DURATION

            self.start_time = datetime.now()
            self.is_monitoring = True

            if max_duration:
                self.auto_stop_timer = threading.Timer(max_duration, self.stop_monitoring)
                self.auto_stop_timer.daemon = True
                self.auto_stop_timer.start()
                logger.info(f"Авто-стоп установлен на {max_duration} секунд")

            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()

            logger.info("Мониторинг запущен")
            return True

        except Exception as e:
            logger.error(f"Ошибка при запуске мониторинга: {e}")
            return False

    def _monitoring_loop(self):
        iteration = 0

        while self.is_monitoring:
            iteration += 1
            logger.info(f"Итерация мониторинга #{iteration}")

            try:
                from utils import monitor_sber_stock
                result = monitor_sber_stock()

                if result and result.get('price') not in ['N/A', 'ERROR']:
                    self.update_stats(success=True)
                    logger.info(f"Успешно: цена {result.get('price')}")
                else:
                    self.update_stats(success=False, error_message="No valid data")
                    logger.warning("Данные не получены")

            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
                self.update_stats(success=False, error_message=str(e))
            wait_time = 0
            while wait_time < MONITORING_INTERVAL and self.is_monitoring:
                time.sleep(1)
                wait_time += 1

        logger.info("Цикл мониторинга завершен")

    def stop_monitoring(self):
        try:
            self.is_monitoring = False

            if self.auto_stop_timer:
                self.auto_stop_timer.cancel()

            logger.info("Мониторинг остановлен")
            self.save_stats()

        except Exception as e:
            logger.error(f"Ошибка при остановке: {e}")

    def update_stats(self, success=True, error_message=None):
        self.monitoring_stats['total_runs'] += 1

        if success:
            self.monitoring_stats['successful_runs'] += 1
            self.monitoring_stats['last_success'] = datetime.now().isoformat()
        else:
            self.monitoring_stats['failed_runs'] += 1
            self.monitoring_stats['last_error'] = error_message

    def get_stats(self):
        stats = self.monitoring_stats.copy()

        if self.start_time:
            duration = datetime.now() - self.start_time
            stats['duration_seconds'] = duration.total_seconds()
            stats['is_active'] = self.is_monitoring

        return stats

    def save_stats(self, filename="monitoring_stats.json"):
        try:
            stats = self.get_stats()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.info(f"Статистика сохранена в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")


monitoring_manager = MonitoringManager()