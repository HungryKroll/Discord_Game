# ui\selectors\quantity_selector.py
import discord
import logging
from models.item import Item
from models.inventory import InventoryManager
from models.storage import StorageType
from ui.base_menu import BaseMenu, BaseButton


class ItemQuantitySelect(discord.ui.Select):
    def __init__(self, user, item, show_item_details, max_quantity=10):
        """
        Инициализация селектора для выбора количества предметов.
        """
        options = [
            discord.SelectOption(
                label=f"{qty} шт. - {item['price'] * qty} 💰",
                value=str(qty)
            ) for qty in range(1, max_quantity + 1)
        ]

        super().__init__(
            placeholder="Выберите количество",
            min_values=1,
            max_values=1,
            options=options
        )
        self.user = user
        self.item = item
        self.show_item_details = show_item_details  # Должен быть передан явно

    async def callback(self, interaction: discord.Interaction):
        """
        Обработчик выбора количества.
        """
        quantity = int(self.values[0])

        destination_view = discord.ui.View()
        destination_view.add_item(
            DestinationButton(
                self.user,
                self.item,
                quantity,
                destination="🎒 Инвентарь",
            )
        )
        destination_view.add_item(
            DestinationButton(
                self.user,
                self.item,
                quantity,
                destination="🔧 Снаряжение",
            )
        )

        back_button = BaseButton(
            "Назад 🔙",
            self.user,
            callback=self.show_item_details
        )
        destination_view.add_item(back_button)

        await interaction.response.edit_message(
            content=f"Выберите место для {quantity} × {self.item['name']}",
            view=destination_view
        )

class DestinationButton(discord.ui.Button):
    def __init__(self, user, item, quantity, destination):
        """
        Инициализация кнопки для выбора места добавления предмета.
        """
        super().__init__(label=f"Добавить в {destination}", style=discord.ButtonStyle.primary)
        self.user = user
        self.item = item
        self.quantity = quantity
        self.destination = destination

    async def callback(self, interaction: discord.Interaction):
        """
        Обработчик нажатия кнопки добавления предмета.
        """
        try:
            result = await InventoryManager.move_item(
                user_id=self.user.id,
                item_id=self.item['id'],
                quantity=self.quantity,
                from_storage=StorageType.EQUIPMENT if self.destination == "🎒 Инвентарь" else StorageType.INVENTORY,
                to_storage=StorageType.INVENTORY if self.destination == "🎒 Инвентарь" else StorageType.EQUIPMENT
            )
            await interaction.response.send_message(
                f"✅ {self.quantity} × {self.item['name']} перемещено в {self.destination}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Ошибка перемещения: {str(e)}")
            await interaction.response.send_message("❌ Не удалось переместить предмет", ephemeral=True)
