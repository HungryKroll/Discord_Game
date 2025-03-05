# ui\base_menu.py
# КОММЕНТАРИЙ:
# Базовые классы для создания интерактивных меню

import discord
import logging


class BaseMenu(discord.ui.View):
    """
    Базовый класс для создания интерактивных меню
    """

    def __init__(self, user, *buttons):
        super().__init__()
        self.user = user
        for button in buttons:
            self.add_item(button)

class BaseButton(discord.ui.Button):
    """
    Базовая кнопка с расширенной функциональностью
    """

    def __init__(self, label, user, style=discord.ButtonStyle.primary, callback=None, custom_id=None):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.user = user
        self.custom_callback = callback

    async def callback(self, interaction: discord.Interaction):
        """
        Обработчик нажатия кнопки с проверкой пользователя
        """
        if interaction.user != self.user:
            await interaction.response.send_message(
                "Это меню не для вас.",
                ephemeral=True
            )
            return

        logging.info(f"{interaction.user.name} нажал кнопку: {self.label}")

        if self.custom_callback:
            await self.custom_callback(interaction)

class PaginationButton(BaseButton):
    def __init__(self, label, user, offset):
        """
        Кнопка для пагинации.
        :param label: Текст на кнопке (например, "Вперёд" или "Назад").
        :param user: Пользователь, для которого создаётся кнопка.
        :param offset: Смещение страницы (например, +1 для "Вперёд", -1 для "Назад").
        """
        super().__init__(label=label, user=user)
        self.offset = offset  # -1 для "Назад", +1 для "Вперед"

    async def callback(self, interaction: discord.Interaction):
        """
        Обработчик нажатия кнопки.
        """
        current_page = getattr(self.view, "current_page", 0)
        self.view.current_page = max(0, current_page + self.offset)
        await self.view.update_items()  # Этот метод нужно реализовать в меню
