# raid|raid_manager.py
# КОММЕНТАРИЙ:
# Управление рейдами с основным каналом и приватными ветками
# Основной канал статичный, приватные ветки создаются динамически

import discord
import logging
from config.database import execute_query, fetch_query
from models.enemy import Enemy

class RaidManager:
    def __init__(self, guild, user, main_raid_channel_id):
        """
        Инициализация менеджера рейда

        ИСПОЛЬЗОВАНИЕ:
        raid = RaidManager(guild, user, main_raid_channel_id)
        """
        self.guild = guild
        self.user = user
        self.main_raid_channel_id = main_raid_channel_id
        self.thread = None
        self.enemy = None

    async def create_raid_thread(self):
        """
        Создание приватной ветки рейда в основном канале

        ИСПОЛЬЗОВАНИЕ:
        thread = await raid.create_raid_thread()
        """
        try:
            main_channel = self.guild.get_channel(self.main_raid_channel_id)

            if not main_channel:
                logging.error(f"Основной канал рейда с ID {self.main_raid_channel_id} не найден")
                return None

            thread_name = f"Рейд-{self.user.display_name.lower().replace(' ', '-')}"

            # Создание приватной ветки
            self.thread = await main_channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread,
                auto_archive_duration=60
            )

            # Добавление пользователя в ветку
            await self.thread.add_user(self.user)

            # Сохранение ветки в базе данных
            insert_result = await execute_query(
                "INSERT INTO raid_threads (thread_id, user_id, main_channel_id) VALUES (?, ?, ?)",
                (self.thread.id, self.user.id, self.main_raid_channel_id)
            )

            if insert_result:
                logging.info(f"Создана приватная ветка рейда: {thread_name}")
                return self.thread
            else:
                logging.error(f"Не удалось сохранить ветку в базе данных: {thread_name}")
                await self.thread.delete()
                return None

        except discord.Forbidden:
            logging.error(f"Недостаточно прав для создания ветки рейда. Пользователь: {self.user}")
            await self.user.send("Не удалось создать ветку рейда. Недостаточно прав.")
        except Exception as e:
            logging.error(f"❌ Критическая ошибка при создании ветки рейда: {e}")

        return None

    async def generate_enemy(self):
        """
        Генерация врага для рейда

        ИСПОЛЬЗОВАНИЕ:
        await raid.generate_enemy()
        """
        enemy_data = await Enemy.get_random_enemy()
        if enemy_data:
            self.enemy = Enemy(
                name=enemy_data["name"],
                category=enemy_data["category"],
                strong=enemy_data["strong"],
                life=enemy_data["life"],
                allow_weapon=enemy_data["allow_weapon"],
                allow_other_items=enemy_data["allow_other_items"]
            )

            # Экипировка врага предметами
            if self.enemy.allow_weapon:
                weapon = await Enemy.get_random_item_by_category("оружие")
                if weapon:
                    self.enemy.equip_weapon(weapon[0])

            if self.enemy.allow_other_items:
                other_item = await Enemy.get_random_item_by_category(exclude_category="оружие")
                if other_item:
                    self.enemy.equip_other_item(other_item[0])

            return self.enemy
        return None

    async def close_raid_thread(self):
        """
        Закрытие ветки рейда

        ИСПОЛЬЗОВАНИЕ:
        await raid.close_raid_thread()
        """
        if self.thread:
            try:
                thread_id = self.thread.id
                delete_result = await execute_query(
                    "DELETE FROM raid_threads WHERE thread_id = ?",
                    (thread_id,)
                )

                if delete_result:
                    await self.thread.send("Ветка рейда будет закрыта через 10 секунд...")
                    await discord.asyncio.sleep(10)
                    await self.thread.delete()
                    logging.info(f"Ветка рейда {thread_id} успешно удалёна.")
                else:
                    logging.warning(f"Не удалось удалить запись о ветке {thread_id} из базы данных")

            except discord.HTTPException as e:
                logging.error(f"❌ Ошибка HTTP при удалении ветки рейда: {e}")
            except Exception as e:
                logging.error(f"❌ Ошибка при закрытии ветки рейда: {e}")

    @staticmethod
    async def close_all_raid_threads(guild, main_raid_channel_id):
        """
        Закрытие всех веток рейдов в основном канале

        ИСПОЛЬЗОВАНИЕ:
        closed_threads = await RaidManager.close_all_raid_threads(guild, main_raid_channel_id)
        """
        closed_threads = []
        try:
            raid_thread_ids = await fetch_query(
                "SELECT thread_id FROM raid_threads WHERE main_channel_id = ?",
                (main_raid_channel_id,)
            )

            if not raid_thread_ids:
                logging.info("Нет активных веток рейдов для закрытия")
                return closed_threads

            for thread_id in [row[0] for row in raid_thread_ids]:
                thread = guild.get_thread(thread_id)
                if thread:
                    try:
                        await thread.delete()
                        closed_threads.append(thread.name)
                        logging.info(f"Ветка рейда {thread.name} удалёна")
                    except discord.HTTPException as e:
                        logging.error(f"Не удалось удалить ветку {thread.name}: {e}")
                    except Exception as e:
                        logging.error(f"❌ Ошибка при удалении ветки {thread.name}: {e}")

                    await execute_query("DELETE FROM raid_threads WHERE thread_id = ?", (thread_id,))

        except Exception as e:
            logging.error(f"❌ Критическая ошибка при закрытии веток рейдов: {e}")

        return closed_threads