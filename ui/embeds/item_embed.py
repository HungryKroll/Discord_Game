# ui\embeds\item_embed.py

import discord
from ui.color_palette import ColorPalette

class ItemEmbed:
    @staticmethod
    def create(item):
        """
        Создание embed для детального описания предмета
        """

        embed = discord.Embed(
            title=f"🏷️ {item['name']}",
            description=item.get('description', 'Описание отсутствует'),
            color=ColorPalette.get_color(item['category'])
        )

        # Основные характеристики
        embed.add_field(name="Стоимость", value=f"{item['price']} 💰", inline=True)
        embed.add_field(name="Категория", value=item['category'], inline=True)

        # Новые поля
        if item['category'] in ['оружие', 'щит', 'броня']:
            if 'evasion' in item:
                embed.add_field(name="Уклонение", value=item['evasion'], inline=True)

            if item['category'] == 'оружие' and 'hand_slot' in item:
                hand_type = "Двуручное" if item['hand_slot'] == 2 else "Одноручное"
                embed.add_field(name="Тип оружия", value=hand_type, inline=True)

        # Дополнительные параметры
        if item.get('Dmg'):
            embed.add_field(name="Урон", value=item['Dmg'], inline=True)
        if item.get('Arm'):
            embed.add_field(name="Защита", value=item['Arm'], inline=True)

        return embed
