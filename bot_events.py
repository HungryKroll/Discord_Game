# bot_events.py
import os
import logging
import asyncio
import traceback
import discord
from config.session_manager import SessionManager
from config.logger import safe_execute
from config.database import execute_query, fetch_query, close_db

class BotEvents:
    @staticmethod
    async def on_ready(bot):
        """Обработчик события готовности бота"""
        logging.info("🚀 Начало события on_ready")
        print("🔄 Инициализация бота...")

        # Получение ID основных каналов из .env
        CAMP_CHANNEL_ID = int(os.getenv('camp_channel_ID'))
        RAID_CHANNEL_ID = int(os.getenv('raid_channel_ID'))
        main_channel_ids = [CAMP_CHANNEL_ID, RAID_CHANNEL_ID]

        try:
            # Проверка сессии через SessionManager
            session = await SessionManager().get_session()
            if session:
                logging.info("✅ aiohttp-сессия успешно создана")
            else:
                logging.warning("❌ Не удалось создать aiohttp-сессию")

            # Получение информации о серверах
            guild = discord.utils.get(bot.guilds, name="Бототестер")
            if guild:
                bot_member = guild.get_member(bot.user.id)
                logging.info("🔑 Роли бота на сервере:")
                for role in bot_member.roles:
                    logging.info(f"- {role.name} (ID: {role.id})")
            else:
                logging.warning("❌ Сервер не найден.")

            # Извлечение списка всех потоков
            try:
                threads = await fetch_query("SELECT threads_id, user_id, thread_type FROM threads")

            except Exception as e:
                logging.warning(f"⚠️ Ошибка при получении потоков: {e}")
                threads = []

            # Статистика потоков
            total_threads = len(threads)
            invalid_threads = 0
            invalid_main_threads = 0
            thread_types = {'camp': 0, 'raid': 0}

            # Проверка валидности потоков
            for row in threads:
                thread_id, user_id, thread_type = row[0], row[1], row[2]
                thread = bot.get_channel(thread_id)

                # Проверка существования потока
                if thread is None:
                    invalid_threads += 1
                    logging.warning(f"❌ Поток с ID {thread_id} типа {thread_type} не существует.")

                    # Удаление несуществующего потока из базы данных
                    await safe_execute(
                        execute_query,
                        "DELETE FROM threads WHERE threads_id = ?",
                        (thread_id,)
                    )
                else:
                    # Проверка принадлежности к основным каналам
                    parent_channel_id = thread.parent_id if isinstance(thread, discord.Thread) else thread.id

                    if parent_channel_id not in main_channel_ids:
                        invalid_main_threads += 1
                        logging.warning(
                            f"⚠️ Поток {thread_id} типа {thread_type} "
                            f"не принадлежит основным каналам. "
                            f"Родительский канал: {parent_channel_id}"
                        )

                        # Удаление потока, не связанного с основными каналами
                        await safe_execute(
                            execute_query,
                            "DELETE FROM threads WHERE threads_id = ?",
                            (thread_id,)
                        )
                    else:
                        # Подсчет типов потоков
                        thread_types[thread_type] += 1

            # Логирование статистики потоков
            logging.info(f"📊 Статистика потоков:")
            logging.info(f"- Всего потоков: {total_threads}")
            logging.info(f"- Лагерей: {thread_types['camp']}")
            logging.info(f"- Рейдов: {thread_types['raid']}")
            logging.info(f"- Невалидных потоков: {invalid_threads}")
            logging.info(f"- Потоков вне основных каналов: {invalid_main_threads}")

            # Уведомление о проблемных потоках
            if invalid_threads > 0 or invalid_main_threads > 0:
                logging.warning(
                    f"🧹 Удалено {invalid_threads} несуществующих потоков "
                    f"и {invalid_main_threads} потоков вне основных каналов"
                )
            print(f"🤖 Бот готов. Вошли как {bot.user}")
            logging.info(f"Бот успешно инициализирован. Пользователь: {bot.user}")

        except Exception as e:
            logging.critical(
                f"❌ Критическая ошибка при инициализации бота: {e}\n"
                f"Трассировка: {traceback.format_exc()}"
            )
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при инициализации: {e}")

        # Добавлен блок finally (опционально)
        finally:
            logging.info("Завершение процедуры инициализации бота")

    @staticmethod
    async def close_bot_gracefully(bot):
        """Корректное завершение работы бота"""
        logging.info("🔄 Начало корректного завершения работы бота...")

        try:
            # Отключение бота от Discord
            if not bot.is_closed():
                logging.info("🔌 Отключение от Discord...")
                await bot.close()

            # Закрытие всех задач
            pending_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if pending_tasks:
                logging.info(f"📋 Завершаем {len(pending_tasks)} задач...")
                for task in pending_tasks:
                    task.cancel()
                await asyncio.gather(*pending_tasks, return_exceptions=True)
                logging.info("✅ Все задачи завершены.")

            # Закрытие дополнительных ресурсов
            await SessionManager().close_session()
            await close_db()

            logging.info("✅ Бот успешно завершил работу")

        except Exception as e:
            logging.error(f"❌ Ошибка при завершении работы: {e}")
            logging.error(f"Трассировка: {traceback.format_exc()}")
