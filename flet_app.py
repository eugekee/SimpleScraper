import flet as ft
import pandas as pd
from datetime import datetime
import threading
import time
import os
from utils import read_excel_data, monitor_sber_stock
from config import EXCEL_FILE, MONITORING_INTERVAL
import logging

logger = logging.getLogger(__name__)


class SberMonitorApp:
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.page = None

    def main(self, page: ft.Page):
        self.page = page
        page.title = "Мониторинг акций Сбербанка"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.scroll = ft.ScrollMode.ADAPTIVE

        self.status_text = ft.Text("Статус: Ожидание", size=16, weight=ft.FontWeight.BOLD)
        self.price_text = ft.Text("Цена: -", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.change_text = ft.Text("Изменение: -", size=16)
        self.last_update = ft.Text("Последнее обновление: -", size=14)

        self.start_btn = ft.ElevatedButton(
            "Запуск мониторинга",
            on_click=self.start_monitoring,
            icon=ft.icons.PLAY_ARROW
        )

        self.stop_btn = ft.ElevatedButton(
            "Остановка мониторинга",
            on_click=self.stop_monitoring,
            icon=ft.icons.STOP,
            disabled=True
        )

        self.single_update_btn = ft.ElevatedButton(
            "Единочное обновление",
            on_click=self.single_update,
            icon=ft.icons.REFRESH
        )

        self.open_excel_btn = ft.ElevatedButton(
            "Открыть Excel файл",
            on_click=self.open_excel_file,
            icon=ft.icons.OPEN_IN_NEW
        )

        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Время")),
                ft.DataColumn(ft.Text("Цена")),
                ft.DataColumn(ft.Text("Изменение")),
                ft.DataColumn(ft.Text("Источник")),
            ],
            rows=[],
        )

        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("График цен", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("График сохраняется в Excel файл", size=14),
                ft.Image(src="chart_placeholder.png", width=400, height=200)
            ]),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
        )

        control_row = ft.Row([
            self.start_btn,
            self.stop_btn,
            self.single_update_btn,
            self.open_excel_btn,
        ], spacing=10)

        status_section = ft.Column([
            self.status_text,
            self.price_text,
            self.change_text,
            self.last_update,
        ], spacing=5)

        page.add(
            ft.Text("Мониторинг акций Сбербанка", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            status_section,
            ft.Divider(),
            control_row,
            ft.Divider(),
            ft.Text("История данных", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=self.data_table,
                height=200,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                padding=10,
            ),
            ft.Divider(),
            self.chart_container,
        )

        self.load_data()

    def start_monitoring(self, e):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()

            self.start_btn.disabled = True
            self.stop_btn.disabled = False
            self.status_text.value = "Статус: Мониторинг запущен"
            self.page.update()

    def stop_monitoring(self, e):
        self.is_monitoring = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.status_text.value = "Статус: Мониторинг остановлен"
        self.page.update()

    def single_update(self, e):
        threading.Thread(target=self.update_data, daemon=True).start()

    def monitoring_loop(self):
        while self.is_monitoring:
            self.update_data()
            time.sleep(MONITORING_INTERVAL)

    def update_data(self):
        try:
            result = monitor_sber_stock()
            if result:

                def update_ui():
                    price = result.get('price', 'N/A')
                    change = result.get('change', 'N/A')
                    change_percent = result.get('change_percent', 'N/A')
                    timestamp = result.get('timestamp', 'N/A')
                    source = result.get('source', 'N/A')

                    self.price_text.value = f"Цена: {price} руб."
                    self.change_text.value = f"Изменение: {change} ({change_percent}%)"
                    self.last_update.value = f"Последнее обновление: {timestamp}"

                    if change != 'N/A' and change != 'SCRAPE_ERROR':
                        try:
                            change_val = float(change.replace(',', '.'))
                            if change_val >= 0:
                                self.change_text.color = ft.Colors.GREEN
                            else:
                                self.change_text.color = ft.Colors.RED
                        except:
                            self.change_text.color = ft.Colors.BLACK

                    self.status_text.value = "Статус: Данные обновлены"
                    self.page.update()
                    self.load_data()

                self.page.run_task(update_ui)

        except Exception as e:
            logger.error(f"Ошибка при обновлении данных: {e}")

            def show_error():
                self.status_text.value = f"Статус: Ошибка - {str(e)}"
                self.page.update()

            self.page.run_task(show_error)

    def load_data(self):
        try:
            df = read_excel_data()
            if not df.empty:
                recent_data = df.tail(10).iloc[::-1]

                rows = []
                for _, row in recent_data.iterrows():
                    rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(row.get('timestamp', 'N/A')))),
                            ft.DataCell(ft.Text(str(row.get('price', 'N/A')))),
                            ft.DataCell(ft.Text(f"{row.get('change', 'N/A')} ({row.get('change_percent', 'N/A')}%)")),
                            ft.DataCell(ft.Text(str(row.get('source', 'N/A')))),
                        ])
                    )

                self.data_table.rows = rows
                self.page.update()

        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")

    def open_excel_file(self, e):
        try:
            if os.path.exists(EXCEL_FILE):
                os.startfile(EXCEL_FILE)
            else:
                self.show_snackbar("Excel файл не найден")
        except Exception as e:
            logger.error(f"Ошибка при открытии файла: {e}")
            self.show_snackbar(f"Ошибка: {str(e)}")

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(content=ft.Text(message))
        self.page.snackbar = snackbar
        snackbar.open = True
        self.page.update()


def run_flet_app():
    app = SberMonitorApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    run_flet_app()