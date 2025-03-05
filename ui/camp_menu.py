# ui\camp_menu.py
# КОММЕНТАРИЙ:
# Меню лагеря с основными действиями

import discord
import logging
from ui.base_menu import BaseMenu, BaseButton
from models.character import Character
from models.inventory import InventoryManager
from ui.trade_menu import TradeMenu
from ui.inventory_menu import InventoryMenu
from ui.equipment_menu import EquipmentMenu


class CampMenu(BaseMenu):

    @classmethod
    async def create(cls, user):
        """
        Асинхронный метод создания экземпляра CampMenu.
        """
        logging.info(f"Создание меню лагеря для пользователя: {user}")
        character = await Character.get_from_db(user.id)

        # Получаем сумму золота из инвентаря и снаряжения
        money = await InventoryManager.get_gold(user.id)  # Добавлен await

        instance = cls(user)
        instance.character = character
        instance.money = money

        logging.info(f"Меню лагеря создано. Золото пользователя: {money}")
        return instance

    def __init__(self, user):
        """Стандартный инициализатор без асинхронных вызовов."""
        logging.debug("Инициализация CampMenu")

        # Кнопка для открытия магазина (торговля)
        store_button = BaseButton(
            label="Магазин 🛒",
            user=user,
            callback=self.open_store,
            style=discord.ButtonStyle.primary
        )

        # Кнопка для открытия снаряжения
        equipment_button = BaseButton(
            label="Снаряжение 🔧",
            user=user,
            callback=self.open_equipment,
            style=discord.ButtonStyle.secondary
        )

        # Кнопка для открытия инвентаря
        inventory_button = BaseButton(
            label="Инвентарь 🎒",
            user=user,
            callback=self.open_inventory,
            style=discord.ButtonStyle.green
        )

        # Добавляем кнопки в меню
        super().__init__(
            user,
            store_button,
            equipment_button,
            inventory_button
        )

        self.user = user
        self.character = None
        self.money = 0

    async def open_store(self, interaction: discord.Interaction):
        """
        Открытие меню торговли.
        """
        try:
            trade_menu = await TradeMenu.create(interaction.user)
            await interaction.response.edit_message(view=trade_menu)
            logging.info(f"Магазин успешно открыт для {interaction.user}")
        except Exception as e:
            logging.error(f"Ошибка открытия магазина: {e}")
            await interaction.followup.send(
                content="Не удалось открыть магазин.",
                ephemeral=True
            )

    async def open_equipment(self, interaction: discord.Interaction):
        """
        Открытие меню снаряжения.
        """
        try:
            equipment_menu = await EquipmentMenu.create(interaction.user)
            await interaction.response.edit_message(view=equipment_menu)
            logging.info(f"Снаряжение успешно открыто для {interaction.user}")
        except Exception as e:
            logging.error(f"Ошибка открытия снаряжения: {e}")
            await interaction.followup.send(
                content="Не удалось открыть снаряжение.",
                ephemeral=True
            )

    async def open_inventory(self, interaction: discord.Interaction):
        """
        Открытие меню инвентаря.
        """
        try:
            inventory_menu = await InventoryMenu.create(interaction.user)
            await interaction.response.edit_message(
                content=f"💰 Золото: {self.money} | {StorageType.INVENTORY['display']}",
                view=inventory_menu
            )
        except Exception as e:
            logging.error(f"Ошибка открытия инвентаря: {e}")
            await interaction.followup.send("Не удалось открыть инвентарь.", ephemeral=True)

    async def update_balance(self, interaction: discord.Interaction):
        """Обновляет сообщение с текущим балансом."""
        self.money = await InventoryManager.get_gold(self.user.id)
        await interaction.edit_original_response(content=f"💰 Золото: {self.money}")

    async def go_back(self, interaction: discord.Interaction):
        """
        Возврат в главное меню лагеря.
        """
        try:
            from ..camp_menu import CampMenu  # Относительный импорт
            camp_menu = await CampMenu.create(interaction.user)
            await interaction.response.edit_message(view=camp_menu)
            logging.info(f"CampMenu.go_back: Пользователь {interaction.user.id} вернулся в главное меню")
        except Exception as e:
            logging.error(f"CampMenu.go_back: {e} | UserID: {interaction.user.id}")
            await interaction.response.send_message("Произошла ошибка при возврате в главное меню.", ephemeral=True)
