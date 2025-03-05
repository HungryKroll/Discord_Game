# ui\color_palette.py
import discord

class ColorPalette:
    """Цветовая палитра для категорий"""
    COLORS = {
        'оружие': discord.Color.red(),
        'броня': discord.Color.blue(),
        'зелье': discord.Color.green(),
        'хлам': discord.Color.light_grey()
    }

    @classmethod
    def get_color(cls, category):
        return cls.COLORS.get(category, discord.Color.default())
