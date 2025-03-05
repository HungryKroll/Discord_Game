# models\item.py
# КОММЕНТАРИЙ:
# Позволяет получать списки предметов и их категории

import logging
from config.database import fetch_query
import math

# Общий список полей для предметов
ITEM_FIELDS = [
    'id', 'name', 'category', 'weight', 'Dmg', 'Arm',
    'Rest_HP', 'Rest_Mana', 'price', 'description',
    'hand_slot', 'evasion'
]

CATEGORY_FIELDS = ['category', 'count']

class Item:

    @staticmethod
    async def get_item_by_id(item_id):
        """Получение полной информации о предмете с новыми полями"""
        try:
            query = f"""
                SELECT {', '.join(ITEM_FIELDS)}
                FROM items
                WHERE id = ?
            """
            result = await fetch_query(query, (item_id,))
            if result:
                return dict(zip(ITEM_FIELDS, result[0]))
            logging.warning(f"Предмет с ID {item_id} не найден.")
            return None
        except Exception as e:
            logging.error(f"Ошибка получения предмета: {e}")
            return None

    @staticmethod
    async def get_all_categories():
        """Возвращает список всех категорий с количеством предметов."""
        try:
            query = "SELECT category, COUNT(*) as count FROM items GROUP BY category"
            rows = await fetch_query(query)
            return [{"category": row[0], "count": row[1]} for row in rows]
        except Exception as e:
            logging.error(f"Ошибка получения категорий: {e}")
            return []

    @staticmethod
    async def get_items_by_category(category_name):
        """Получение всех предметов указанной категории."""
        try:
            query = f"""
                SELECT {', '.join(ITEM_FIELDS)}
                FROM items
                WHERE category = ?
            """
            rows = await fetch_query(query, (category_name,))
            return [dict(zip(ITEM_FIELDS, row)) for row in rows]
        except Exception as e:
            logging.error(f"Ошибка получения предметов категории '{category_name}': {e}")
            return []

    @staticmethod
    def calculate_price(item, quantity, reputation=50):
        """Расчёт цены с учётом репутации"""
        base_price = item.get('price', 0)
        if reputation < 50:
            multiplier = 1.25
        elif reputation > 50:
            multiplier = 0.75
        else:
            multiplier = 1.0
        return math.ceil(base_price * quantity * multiplier)
