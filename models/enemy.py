# models\enemy.py
# КОММЕНТАРИЙ:
# Модель врага с генерацией и настройкой параметров
# Поддерживает экипировку оружием и предметами

from config.database import fetch_query
import logging
import random

class Enemy:
    def __init__(
        self,
        name,
        category,
        strong,
        life,
        allow_weapon=True,
        allow_other_items=True
    ):
        """
        Инициализация врага с базовыми параметрами

        ИСПОЛЬЗОВАНИЕ:
        enemy = Enemy("Гоблин", "разбойники", 10, 50)
        """
        self.name = name
        self.category = category
        self.strong = strong
        self.life = life
        self.allow_weapon = allow_weapon
        self.allow_other_items = allow_other_items
        self.weapon = None
        self.other_item = None

    def equip_weapon(self, weapon):
        """
        Экипировка оружия

        ИСПОЛЬЗОВАНИЕ:
        enemy.equip_weapon(weapon)
        """
        if self.allow_weapon and weapon:
            self.weapon = weapon
        else:
            logging.warning(f"Невозможно оснастить оружием: {weapon}")

    def equip_other_item(self, item):
        """
        Экипировка дополнительного предмета

        ИСПОЛЬЗОВАНИЕ:
        enemy.equip_other_item(item)
        """
        if self.allow_other_items and item:
            self.other_item = item
        else:
            logging.warning(f"Невозможно оснастить другим предметом: {item}")

    @staticmethod
    async def get_random_enemy():
        """
        Получение случайного врага с модификаторами

        ИСПОЛЬЗОВАНИЕ:
        enemy_data = await Enemy.get_random_enemy()
        """
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute(
                "SELECT category, name, base_strong, base_life, allow_weapon, allow_other_items FROM enemy_categories ORDER BY RANDOM() LIMIT 1"
            ) as cursor:
                enemy_category = await cursor.fetchone()

                if not enemy_category:
                    logging.warning("Не найдены категории врагов")
                    return None

                category, name, base_strong, base_life, allow_weapon, allow_other_items = enemy_category

                # Получаем модификаторы вида
                async with db.execute("""
                    SELECT view, view_strong_modifier, view_life_modifier
                    FROM enemy_modifiers
                    WHERE category = ? ORDER BY RANDOM() LIMIT 1
                """, (category,)) as cursor:
                    view_modifiers = await cursor.fetchone()

                # Получаем модификаторы возраста
                async with db.execute("""
                    SELECT age, age_strong_modifier, age_life_modifier
                    FROM enemy_modifiers
                    WHERE category = ? ORDER BY RANDOM() LIMIT 1
                """, (category,)) as cursor:
                    age_modifiers = await cursor.fetchone()

                if view_modifiers and age_modifiers:
                    view, view_strong_mod, view_life_mod = view_modifiers
                    age, age_strong_mod, age_life_mod = age_modifiers

                    try:
                        # Преобразование модификаторов
                        view_strong_mod = int(view_strong_mod)
                        view_life_mod =int(view_life_mod)
                        age_strong_mod = int(age_strong_mod)
                        age_life_mod = int(age_life_mod)
                    except ValueError as e:
                        logging.warning(f"❌ Ошибка преобразования модификаторов: {e}")
                        view_strong_mod = view_life_mod = age_strong_mod = age_life_mod = 0

                    # Расчет итоговых параметров
                    strong = base_strong + view_strong_mod + age_strong_mod
                    life = base_life + view_life_mod + age_life_mod

                    # Формирование имени с модификаторами
                    if category.lower() == "элементали":
                        name_with_modifiers = f"{age} {name} {view}"
                    else:
                        name_with_modifiers = f"{age} {view} {name}"

                    return {
                        "name": name_with_modifiers,
                        "strong": strong,
                        "life": life,
                        "category": category,
                        "allow_weapon": bool(allow_weapon),
                        "allow_other_items": bool(allow_other_items)
                    }

        return None

    @staticmethod
    async def get_random_item_by_category(category=None, exclude_category=None):
        """
        Получение случайного предмета по категории

        ИСПОЛЬЗОВАНИЕ:
        item = await Enemy.get_random_item_by_category("оружие")
        """
        async with aiosqlite.connect(DATABASE_NAME) as db:
            try:
                if category:
                    async with db.execute(
                        "SELECT name, category FROM items WHERE category = ? ORDER BY RANDOM() LIMIT 1",
                        (category,)
                    ) as cursor:
                        return await cursor.fetchone()

                elif exclude_category:
                    async with db.execute(
                        "SELECT name, category FROM items WHERE category != ? ORDER BY RANDOM() LIMIT 1",
                        (exclude_category,)
                    ) as cursor:
                        return await cursor.fetchone()

                else:
                    async with db.execute("SELECT name, category FROM items ORDER BY RANDOM() LIMIT 1") as cursor:
                        return await cursor.fetchone()

            except Exception as e:
                logging.error(f"❌ Ошибка при получении случайного предмета: {e}")
                return None
