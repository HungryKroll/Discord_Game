# ui\trade_menu.py

import discord
from ui.base_menu import BaseMenu, BaseButton
from models.item import Item
from models.inventory import InventoryManager
from models.storage import StorageType
from models.character import Character
from ui.embeds.item_embed import ItemEmbed
from ui.selectors.quantity_selector import ItemQuantitySelect
import logging


class TradeMenu(BaseMenu):
    @classmethod
    async def create(cls, user):
        """Создает меню торговли с категориями."""
        instance = cls(user)

        # Получаем категории
        categories = await Item.get_all_categories()
        if not categories:
            instance.add_item(BaseButton(
                label="Нет доступных категорий",
                user=user,
                disabled=True
            ))
            return instance

        # Добавляем кнопки для каждой категории
        for category in categories:
            instance.add_item(
                BaseButton(
                    label=f"{category['category']} ({category['count']})",
                    user=user,
                    callback=lambda i, cat=category: instance.show_items_in_category(i, cat['category'])
                )
            )

        # Кнопка "Назад"
        instance.add_item(BaseButton(
            label="Назад 🔙",
            user=user,
            callback=instance.go_back
        ))

        return instance

    async def show_items_in_category(self, interaction: discord.Interaction, category_name: str):
        """Отображает предметы в выбранной категории."""
        items = await Item.get_items_by_category(category_name)
        if not items:
            await interaction.response.send_message(
                f"❌ Нет предметов в категории {category_name}.",
                ephemeral=True
            )
            return

        # Очищаем текущие элементы меню
        self.clear_items()

        # Добавляем кнопки для каждого предмета
        for item in items:
            self.add_item(
                BaseButton(
                    label=f"{item['name']} 💰{item['price']}",
                    user=interaction.user,
                    callback=lambda i, it=item: self.buy_item(i, it)
                )
            )

        # Кнопка "Назад"
        self.add_item(BaseButton(
            label="Назад 🔙",
            user=interaction.user,
            callback=self.go_back
        ))

        # Обновляем сообщение
        await interaction.response.edit_message(view=self)

    async def buy_item(self, interaction: discord.Interaction, item):
        """Покупка предмета."""
        try:
            # Получаем информацию о предмете
            item_details = await Item.get_item_by_id(item['id'])
            if not item_details:
                await interaction.response.send_message("❌ Предмет не найден.", ephemeral=True)
                return

            # Создаем embed с описанием предмета
            embed = ItemEmbed.create(item_details)

            # Создаем селектор для выбора количества
            quantity_selector = ItemQuantitySelect(
                user=interaction.user,
                item=item_details,
                show_item_details=lambda i: self.show_items_in_category(i, item_details['category']),
                max_quantity=10
            )

            # Создаем view с селектором
            view = discord.ui.View()
            view.add_item(quantity_selector)

            # Отправляем сообщение с embed и селектором
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Ошибка покупки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при покупке.", ephemeral=True)

    async def go_back(self, interaction: discord.Interaction):
        """Возврат к списку категорий"""
        self.clear_items()
        categories = await Item.get_all_categories()

        for category in categories:
            self.add_item(
                BaseButton(
                    label=f"{category['category']} ({category['count']})",
                    user=interaction.user,
                    callback=lambda i, cat=category: self.show_items_in_category(i, cat['category'])
                )
            )

        self.add_item(BaseButton(
            label="Назад 🔙",
            user=interaction.user,
            callback=lambda i: self.go_back_to_camp(i)
        ))

        await interaction.response.edit_message(view=self)

    async def go_back_to_camp(self, interaction: discord.Interaction):
        """Возврат в главное меню лагеря"""
        from ui.camp_menu import CampMenu
        camp_menu = await CampMenu.create(interaction.user)
        await interaction.response.edit_message(view=camp_menu)
