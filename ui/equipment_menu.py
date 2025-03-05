# ui\equipment_menu.py

import discord
from ui.base_menu import BaseMenu, BaseButton
from models.item import Item
from models.inventory import InventoryManager
from models.storage import StorageType
from ui.embeds.item_embed import ItemEmbed
from ui.selectors.quantity_selector import ItemQuantitySelect
import logging

class EquipmentMenu(BaseMenu):
    @classmethod
    async def create(cls, user):
        """
        Создание меню снаряжения.
        """

        items = await InventoryManager.get_items(user.id, StorageType.EQUIPMENT)
        instance = cls(user)

        back_button = BaseButton(
            label="Назад 🔙",
            user=user,
            callback=cls.go_back
        )
        instance.add_item(back_button)

        return instance

        if not items:
            logging.info(f"Снаряжение пользователя {user} пусто")
        else:
            logging.info(f"Снаряжение пользователя {user} загружено")

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
                storage=StorageType.EQUIPMENT
            )

            if success:
                await interaction.response.send_message(
                    f"✅ {item['name']} успешно продан из 🔧 снаряжения",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Не удалось продать предмет из 🔧 снаряжения",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Ошибка продажи: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при продаже из 🔧 снаряжения",
                ephemeral=True
            )

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
                from_storage=StorageType.EQUIPMENT,
                to_storage=StorageType.INVENTORY
            )

            if success:
                await interaction.response.send_message(
                    f"✅ {item['name']} перемещено из 🔧 снаряжения в 🎒 инвентарь",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Не удалось переместить предмет из 🔧 снаряжения в 🎒 инвентарь",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Ошибка перемещения: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при перемещении из 🔧 снаряжения в 🎒 инвентарь",
                ephemeral=True
            )

    @staticmethod
    async def go_back(interaction: discord.Interaction):
        from ui.camp_menu import CampMenu
        try:
            camp_menu = await CampMenu.create(interaction.user)
            await interaction.response.edit_message(view=camp_menu)
        except Exception as e:
            logging.error(f"EquipmentMenu.go_back: {e}")
            await interaction.response.send_message("❌ Ошибка возврата", ephemeral=True)

class EquipmentValidator:
    @staticmethod
    async def validate_equipment(user_id: int, new_item: Item) -> bool:
        equipped = await get_equipped_items(user_id)  # Получить экипировку из БД

        # Считаем занятые руки и проверяем типы
        total_hands = 0
        has_two_handed = False
        has_shield = False

        for item in equipped:
            if item.category == "оружие":
                total_hands += item.hand_slot
                if item.hand_slot == 2:
                    has_two_handed = True
            elif item.category == "щит":
                total_hands += 1
                has_shield = True

        # Проверка для нового предмета
        if new_item.category == "оружие":
            if new_item.hand_slot == 2:
                # Двуручное оружие можно экипировать только в пустые руки
                return total_hands == 0
            else:
                # Одноручное оружие: руки не заняты двуручным, и есть место
                return not has_two_handed and (total_hands + 1) <= 2

        elif new_item.category == "щит":
            # Щит можно экипировать только с одноручным оружием
            return not has_two_handed and (total_hands + 1) <= 2

        else:
            # Броня и прочее экипируется без ограничений
            return True
