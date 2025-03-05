# utils\signal_handler
import asyncio
import signal
import logging
import sys
import traceback

class GracefulExit:
    def __init__(self, bot):
        self.bot = bot
        self.is_shutting_down = False
        self.shutdown_timeout = 10  # Таймаут завершения в секундах

    async def handle_signals(self):
        """Обработка сигналов завершения"""
        try:
            loop = asyncio.get_running_loop()

            if sys.platform == "win32":
                def windows_signal_handler():
                    asyncio.create_task(self.shutdown())

                import win32api
                win32api.SetConsoleCtrlHandler(windows_signal_handler, True)
                logging.info("✅ Установлен обработчик сигналов для Windows")
            else:
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(
                        sig,
                        lambda s=sig: asyncio.create_task(self.shutdown(s))
                    )
                logging.info("✅ Установлен обработчик сигналов для Unix")
        except Exception as e:
            logging.error(f"❌ Ошибка установки обработчика сигналов: {e}")

    async def shutdown(self, signal=None):
        """Корректное завершение работы с принудительным таймаутом"""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        signal_name = signal.name if signal else "Принудительное завершение"
        logging.info(f"🛑 Получен сигнал {signal_name}. Начало завершения...")

        try:
            # Создаем список всех текущих задач
            pending_tasks = [
                task for task in asyncio.all_tasks()
                if task is not asyncio.current_task()
            ]

            if pending_tasks:
                logging.info(f"📋 Завершаем {len(pending_tasks)} задач...")

                # Отменяем все задачи
                for task in pending_tasks:
                    task.cancel()

                # Ждем завершения с таймаутом
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*pending_tasks, return_exceptions=True),
                        timeout=self.shutdown_timeout
                    )
                except asyncio.TimeoutError:
                    logging.warning("⏰ Не все задачи завершены в течение таймаута")

            # Закрытие бота и сессий
            if hasattr(self.bot, 'close'):
                await self.bot.close()

            # Закрытие базы данных и других ресурсов
            from config.database import close_db
            from config.session_manager import SessionManager

            await close_db()
            await SessionManager.close_session()

            logging.info("✅ Бот успешно завершил работу")

        except Exception as e:
            logging.error(f"❌ Ошибка при завершении работы: {e}")
            logging.error(traceback.format_exc())

        finally:
            # Принудительное завершение цикла событий
            loop = asyncio.get_event_loop()
            loop.stop()
            sys.exit(0)
