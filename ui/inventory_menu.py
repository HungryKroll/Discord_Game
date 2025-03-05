# ui\inventory_menu.py
import discord
from ui.base_menu import BaseMenu, BaseButton
from models.item import Item
from models.inventory import InventoryManager
from models.storage import StorageType
from ui.embeds.item_embed import ItemEmbed
from ui.selectors.quantity_selector import ItemQuantitySelect
from ui.base_storage_menu import StorageMenu
import logging

class InventoryMenu(StorageMenu):
    def __init__(self, user):
        super().__init__(user, StorageType.INVENTORY)

    @classmethod
    async def create(cls, user):
        instance = cls(user)
        await instance.load_items()  # Вызов метода от экземпляра
        await instance.update_view()

        back_button = BaseButton(
            label="Назад 🔙",
            user=user,
            callback=instance.go_back
        )
        instance.add_item(back_button)

        return instance


    @staticmethod
    async def handle_move(self, interaction: discord.Interaction, item):
        """
        Обработчик перемещения предмета
        """
        try:
            success = await InventoryManager.move_item(
                user_id=interaction.user.id,
                item_id=item['id'],
                quantity=item['quantity'],
                from_storage=StorageType.INVENTORY,
                to_storage=StorageType.EQUIPMENT
            )

            if success:
                await interaction.response.send_message(
                    f"✅ {item['name']} перемещено в из 🎒 инвентаря в 🔧 снаряжение",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Не удалось переместить предмет из 🎒 инвентаря в 🔧 снаряжение",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Ошибка перемещения: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при перемещении из 🎒 инвентаря в 🔧 снаряжение",
                ephemeral=True
            )

    @staticmethod
    async def handle_sell(self, interaction: discord.Interaction, item):
        """
        Обработчик продажи предмета
        """
        try:
            success = await InventoryManager.sell_item(
                user_id=interaction.user.id,
                item_id=item['id'],
                quantity=item['quantity'],
                storage=StorageType.INVENTORY
            )

            if success:
                await interaction.response.send_message(
                    f"✅ {item['name']} успешно продан из 🎒 инвентаря",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Не удалось продать предмет из 🎒 инвентаря",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Ошибка продажи: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при продаже из 🎒 инвентаря",
                ephemeral=True
            )

    @staticmethod
    async def go_back(interaction: discord.Interaction):
        from ui.camp_menu import CampMenu  # Используем абсолютный импорт
        try:
            camp_menu = await CampMenu.create(interaction.user)
            await interaction.response.edit_message(view=camp_menu)
        except Exception as e:
            logging.error(f"InventoryMenu.go_back: {e}")
            await interaction.response.send_message("❌ Ошибка возврата", ephemeral=True)
