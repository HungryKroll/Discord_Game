# main.py
import os
import sys
import asyncio
import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands

# Локальные модули
from config.bot_config import BotConfig
from config.logger import setup_logger, safe_execute
from config.session_manager import SessionManager
from config.database import init_database, close_db
from bot_events import BotEvents
from utils.signal_handler import GracefulExit
from game_commands import setup as setup_game_commands

from ui.camp_menu import CampMenu

async def create_aiohttp_session():
    """Создание aiohttp сессии"""
    session = await SessionManager().get_session()
    if session:
        logging.info("aiohttp сессия создана")
    else:
        logging.error("❌ Ошибка создания aiohttp сессии")

async def main():
    bot = None
    try:
        # Настройка логирования
        setup_logger()

        # Настройка Windows event loop policy
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Инициализация базы данных
        await init_database()

        # Создание интентов
        intents = discord.Intents.default()
        for intent, value in BotConfig.INTENTS_CONFIG.items():
            setattr(intents, intent, value)

        # Создание бота
        bot = commands.Bot(command_prefix='!', intents=intents)

        # Загрузка игровых команд
        await setup_game_commands(bot)

        # Инициализация обработчика сигналов
        graceful_exit = GracefulExit(bot)
        await graceful_exit.handle_signals()

        # Регистрация события on_ready
        @bot.event
        async def on_ready():
            await BotEvents.on_ready(bot)

        # Команда остановки бота
        @bot.command(name='стоп')
        async def stop_bot(ctx):
            if ctx.author.id == BotConfig.OWNER_ID:
                await ctx.send("Инициирую корректную остановку бота...")
                logging.info("Получена команда остановки бота.")
                await BotEvents.close_bot_gracefully(bot)
            else:
                await ctx.send("Эту команду может выполнить только владелец бота.")
                logging.info(f"Попытка остановки бота не владельцем: {ctx.author.id}")

        # Создание aiohttp сессии
        safe_execute(create_aiohttp_session)

        # Запуск бота
        logging.info("Запуск бота...")
        await bot.start(BotConfig.TOKEN)

    except Exception as e:
        logging.critical(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        # Закрытие ресурсов
        if bot is not None:
            await BotEvents.close_bot_gracefully(bot)

        await SessionManager().close_session()
        await close_db()
        logging.info("Программа завершена.")

def shutdown_handler():
    """Принудительное завершение всех задач"""
    try:
        logging.info("🔄 Начало shutdown_handler")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Получаем все незавершенные задачи
        all_tasks = asyncio.all_tasks(loop)
        pending_tasks = [t for t in all_tasks if not t.done()]

        logging.info(f"🔢 Всего задач: {len(all_tasks)}")
        logging.info(f"🚧 Незавершенных задач: {len(pending_tasks)}")

        if pending_tasks:
            logging.info(f"Осталось незавершенных задач: {len(pending_tasks)}")
            for task in pending_tasks:
                task.cancel()

            try:
                loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
            except asyncio.CancelledError:
                logging.info("Все задачи были отменены")
            except Exception as e:
                logging.error(f"Ошибка при отмене задач: {e}")

        loop.close()
        logging.info("Событийный цикл закрыт")

    except Exception as e:
        logging.error(f"Глобальная ошибка в shutdown_handler: {e}", exc_info=True)
    finally:
        logging.info("🏁 Финальный этап shutdown_handler")
        os._exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Принудительная остановка")
    except Exception as e:
        logging.critical(f"❌ Неустранимая ошибка: {e}", exc_info=True)
    finally:
        logging.info("🔍 Вход в shutdown_handler")
        shutdown_handler()
