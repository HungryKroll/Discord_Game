# ui/base_storage_menu.py
import discord
from ui.base_menu import BaseMenu
from models.storage import StorageType


class StorageMenu(BaseMenu):
    ITEMS_PER_PAGE = 10

    def __init__(self, user, storage_type):
        super().__init__(user)
        self.storage_type = storage_type
        self.current_page = 0
        self.total_pages = 0
        self.items = []

    async def load_items(self):
        from models.inventory import InventoryManager

        self.items = await InventoryManager.get_items(self.user.id, self.storage_type.value)
        self.total_pages = (len(self.items) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE

    async def update_view(self):
        self.clear_items()

        # Элементы текущей страницы
        start = self.current_page * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        for item in self.items[start:end]:
            self.add_item(ItemButton(item, self.user, self.storage_type))

        # Контроль пагинации
        if self.total_pages > 1:
            self.add_item(PageButton("⬅️", self.user, -1))
            self.add_item(PageButton("➡️", self.user, 1))

        self.add_item(BackButton(self.user))

    async def show_item_details(self, interaction: discord.Interaction, item):
        """
        Общий метод для отображения деталей предмета
        """
        embed = ItemEmbed.create(item)
        view = discord.ui.View()

        # Кнопка перемещения
        view.add_item(BaseButton(
            label="Переместить 🔄",
            callback=lambda i: self.handle_move(i, item)
        ))

        # Кнопка продажи
        view.add_item(BaseButton(
            label="Продать 💰",
            callback=lambda i: self.handle_sell(i, item)
        ))

        # Кнопка возврата
        view.add_item(BaseButton(
            label="Назад 🔙",
            callback=self.go_back
        ))

        await interaction.response.edit_message(embed=embed, view=view)


class ItemButton(discord.ui.Button):
    def __init__(self, item, user, storage_type):
        super().__init__(
            label=f"{item['name']} × {item['quantity']}",
            style=discord.ButtonStyle.secondary
        )
        self.item = item
        self.user = user
        self.storage_type = storage_type

    async def callback(self, interaction):
        await interaction.response.edit_message(
            view=ItemActionMenu(self.user, self.item, self.storage_type)
        )


class PageButton(discord.ui.Button):
    def __init__(self, label, user, delta):
        super().__init__(label=label)
        self.user = user
        self.delta = delta

    async def callback(self, interaction):
        self.view.current_page = max(0, min(
            self.view.total_pages - 1,
            self.view.current_page + self.delta
        ))
        await self.view.update_view()
        await interaction.response.edit_message(view=self.view)
