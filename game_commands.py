# game_commands.py
import os
import logging
import discord
from discord.ext import commands
from models.character import Character
from models.inventory import InventoryManager
from config.database import execute_query, fetch_query
from ui.camp_menu import CampMenu
from config.logger import setup_logger, safe_execute


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_channel_id = int(os.getenv('raid_channel_ID'))
        self.camp_channel_id = int(os.getenv('camp_channel_ID'))

    async def check_character_exists(self, ctx):
        """
        Универсальный метод проверки персонажа
        """
        if not await Character.exists(ctx.author.id):
            await ctx.send("❌ Персонаж не создан. Используйте команду !новый")
            return False
        return True

    async def clean_up_threads(self, user_id):
        """Удаление веток, которые есть в БД, но отсутствуют в Discord"""
        db_threads = await fetch_query("SELECT threads_id FROM threads WHERE user_id = ?", (user_id,))

        # Получаем объект канала
        camp_channel = self.bot.get_channel(self.camp_channel_id)

        # Получаем все потоки в канале
        discord_threads = {thread.id for thread in camp_channel.threads}  # Убираем вызов методов

        for db_thread in db_threads:
            if db_thread[0] not in discord_threads:  # db_thread - это кортеж, поэтому берём первый элемент
                await execute_query("DELETE FROM threads WHERE threads_id = ?", (db_thread[0],))

    @commands.command(name='лагерь')
    @safe_execute
    async def create_camp(self, ctx):
        if not await self.check_character_exists(ctx):
            return

        # Проверяем, является ли текущий канал лагерем или его веткой
        if ctx.channel.id != self.camp_channel_id and ctx.channel.parent.id != self.camp_channel_id:
            await ctx.send("❌ Лагерь можно создать только в специальном канале или его ветках.")
            return

        character = await Character.get_from_db(ctx.author.id)
        if not character:
            await ctx.send("❌ Сначала создайте персонажа командой !новый")
            return

        # Очистка старых веток
        await self.clean_up_threads(ctx.author.id)

        # Проверяем, существует ли уже лагерь
        existing_thread = await fetch_query("SELECT threads_id FROM threads WHERE user_id = ?", (ctx.author.id,))
        if existing_thread:
            await ctx.send("⚠️ Лагерь уже разбит. Вы можете продолжить использовать его.")
            # Здесь можно отобразить меню лагеря в существующей ветке
            thread = self.bot.get_channel(existing_thread[0][0])  # Получаем объект ветки
            camp_menu = await CampMenu.create(ctx.author)
            await thread.send(content=f"💰 Золото: {camp_menu.money}", view=camp_menu)
            return

        thread = await ctx.channel.create_thread(
            name=f"🏕️ Лагерь {character.stats['name']}",
            type=discord.ChannelType.private_thread
        )

        await thread.add_user(ctx.author)

        await execute_query(
            "INSERT INTO threads (threads_id, user_id, thread_type) VALUES (?, ?, 'camp')",
            (thread.id, ctx.author.id)
        )

        # Создаем меню лагеря
        camp_menu = await CampMenu.create(ctx.author)

        # Отправляем сообщение с меню в созданную ветку
        camp_message = await thread.send(
            content=f"💰 Золото: {camp_menu.money}",
            view=camp_menu
        )

    @commands.command(name='рейд')
    async def create_raid(self, ctx):
        if ctx.channel.id != self.camp_channel_id:
            await ctx.send("❌ Рейд можно начать только в таверне или лагере.")
            return

        character = await Character.get_from_db(ctx.author.id)
        if not character:
            await ctx.send("❌ Сначала создайте персонажа командой !новый")
            return

        # Получаем канал рейдов по его ID
        raid_channel = self.bot.get_channel(int(os.getenv('raid_channel_ID')))

        if not raid_channel:
            await ctx.send("❌ Канал для рейдов не найден.")
            return

        # Создаем ветку в канале рейдов
        thread = await raid_channel.create_thread(
            name=f"🗡️ Рейд {character.name}",
            type=discord.ChannelType.private_thread
        )

        # Получаем последнее сообщение (системное о создании ветки)
        async for message in thread.history(limit=1):
            await message.delete()
            break

        await thread.add_user(ctx.author)

        await execute_query(
            "INSERT INTO threads (threads_id, user_id, thread_type) VALUES (?, ?, 'raid')",
            (thread.id, ctx.author.id)
        )

    @commands.command(name='репа')
    async def set_reputation(self, ctx, delta: int):
        if not await self.check_character_exists(ctx):
            return

        character = await Character.get_from_db(ctx.author.id)
        current_rep = await character.get_reputation()
        new_rep = max(0, min(100, current_rep + delta))

        if await character.update_stat("Reputation", new_rep):

            await ctx.send(f"✅ Репутация {character.name} изменена на {delta}. Текущая: {new_rep}")
        else:
            await ctx.send("❌ Ошибка изменения репутации")

    @commands.command(name='статы')
    async def show_stats(self, ctx):
        if not await self.check_character_exists(ctx):
            return

        character = await Character.get_from_db(ctx.author.id)
        gold_amount = await InventoryManager.get_gold(ctx.author.id)

        stats_embed = discord.Embed(title=f"Статы {character.stats['name']}", color=0x00ff00)
        stats_embed.add_field(name="Здоровье", value=f"{character.health}/{character.max_health}", inline=True)
        stats_embed.add_field(name="Мана", value=f"{character.mana}", inline=True)
        stats_embed.add_field(name="Золото", value=f"{gold_amount} 💰", inline=True)
        stats_embed.add_field(name="Репутация", value=f"{await character.get_reputation()} ⭐", inline=True)

        await ctx.send(embed=stats_embed)

    @commands.command(name='новый')
    async def create_character(self, ctx):
        if await Character.exists(ctx.author.id):
            await ctx.send("❌ Персонаж уже существует.")
            return

        # Создаём персонажа без явного указания имени
        new_character = await Character.create_new_character(ctx.author.id)

        if new_character:
            # Берём имя из БД через метод get_from_db
            character_from_db = await Character.get_from_db(ctx.author.id)
            await ctx.send(f"✅ Персонаж {character_from_db.stats['name']} создан!")
        else:
            await ctx.send("❌ Ошибка при создании персонажа.")

    @commands.command(name='хп')
    async def set_health(self, ctx, amount: int):
        if not await self.check_character_exists(ctx):
            return

        character = await Character.get_from_db(ctx.author.id)

        if await character.update_stats(health_delta=amount):
            sign = "+" if amount >= 0 else ""
            await ctx.send(f"✅ Здоровье {character.name} изменено на {sign}{amount}.")
        else:
            await ctx.send("❌ Ошибка при обновлении здоровья.")

    @commands.command(name='голд')
    async def set_money(self, ctx, delta: int):
        from models.storage import StorageType

        if not await self.check_character_exists(ctx):
            return

        if delta > 0:
            success = await InventoryManager.add_item(
                ctx.author.id,
                InventoryManager.GOLD_ITEM_ID,
                delta,
                StorageType.INVENTORY
            )
        else:
            success = await InventoryManager.remove_item(
                ctx.author.id,
                InventoryManager.GOLD_ITEM_ID,
                abs(delta),
                StorageType.INVENTORY
            )

        if success:
            await ctx.send(f"✅ Золото изменено на {delta} монет")
        else:
            await ctx.send("❌ Ошибка изменения золота")


async def setup(bot):
    await bot.add_cog(GameCommands(bot))
