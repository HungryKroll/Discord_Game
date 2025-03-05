# models\character.py

import logging
from config.database import execute_query, fetch_query
from models.storage import StorageType
from config.logger import setup_logger, safe_execute

# Поля для работы с персонажем
CHARACTER_FIELDS = ['name', 'health', 'mana', 'max_health', 'Reputation']

class Character:
    def __init__(self, user_id, data=None):
        self.user_id = user_id

        # Инициализация основных атрибутов
        if data:
            self.name = data.get('name')
            self.health = data.get('health', 100)
            self.mana = data.get('mana', 50)
            self.max_health = data.get('max_health', 100)
            self.Reputation = data.get('Reputation', 50)
        else:
            self.name = f"Герой_{user_id}"
            self.health = 100
            self.mana = 50
            self.max_health = 100
            self.Reputation = 50

        # Для совместимости со старым кодом
        self.stats = {
            'name': self.name,
            'health': self.health,
            'mana': self.mana,
            'max_health': self.max_health,
            'Reputation': self.Reputation
        }

        self.active_buffs = []

    @classmethod
    async def exists(cls, user_id):
        """
        Проверка существования персонажа в базе данных
        """
        query = "SELECT COUNT(*) FROM characters WHERE user_id = ?"
        try:
            result = await fetch_query(query, (user_id,))
            return result[0][0] > 0
        except Exception as e:
            logging.error(f"❌ Ошибка проверки персонажа: {e}")
            return False

    @classmethod
    @safe_execute
    async def get_from_db(cls, user_id):
        """
        Загрузка персонажа из базы данных с использованием CHARACTER_FIELDS
        """
        try:
            query = f"""
                SELECT {', '.join(CHARACTER_FIELDS)}
                FROM characters
                WHERE user_id = ?
            """
            result = await fetch_query(query, (user_id,))

            if result:
                data = dict(zip(CHARACTER_FIELDS, result[0]))
                return cls(user_id, data)
            return await cls.create_new_character(user_id)

        except Exception as e:
            logging.error(f"Ошибка получения персонажа: {e}")
            return None

    @classmethod
    async def create_new_character(cls, user_id, name=None):
        from models.inventory import InventoryManager
        from models.item import Item
        """
        Создание нового персонажа с инициализацией всех параметров
        """

        try:
            name = name or f"Герой_{user_id}"
            default_values = [name, 100, 50, 100, 50]  # Значения по умолчанию для CHARACTER_FIELDS

            query = f"""
                INSERT INTO characters (user_id, {', '.join(CHARACTER_FIELDS)})
                VALUES (?, ?, ?, ?, ?, ?)
            """
            await execute_query(query, (user_id, *default_values))

            # Добавление стартового золота как предмета
            gold_item = await Item.get_item_by_id(1)  # ID золота в таблице items
            if gold_item:
                await InventoryManager.add_item(user_id, gold_item['id'],
                                                100, StorageType.INVENTORY)  # 100 золота при старте

            return await cls.get_from_db(user_id, data={'name': name})
        except Exception as e:
            logging.error(f"Ошибка создания персонажа: {e}")
            return None

    async def delete_character(self):
        """
        Удаление персонажа и снаряжения при смерти. Инвентарь остаётся.
        """
        from models.inventory import InventoryManager

        try:
            await execute_query("DELETE FROM equipment WHERE user_id = ?", (self.user_id, ))
            logging.info(f"🔧 Снаряжение удалено для пользователя {self.user_id}")

            await execute_query("DELETE FROM characters WHERE user_id = ?", (self.user_id,))
            logging.info(f"Персонаж удалён для пользователя {self.user_id}")

            return True
        except Exception as e:
            logging.error(f"Ошибка удаления персонажа: {e}")
            return False

    async def update_stat(self, stat, value):
        """
        Обновление конкретного параметра персонажа с проверками.
        """
        if stat not in self.stats:
            logging.warning(f"Попытка обновить несуществующий параметр: {stat}")
            return False

        # Проверка для здоровья
        if stat == "health":
            value = max(0, min(self.stats['max_health'], value))  # Здоровье не может быть меньше 0 и больше максимума

        # Проверка для репутации
        if stat == "Reputation":
            value = max(0, min(100, value))  # Репутация не может быть меньше 0 и больше 100

        try:
            self.stats[stat] = value
            query = f"UPDATE characters SET {stat} = ? WHERE user_id = ?"
            await execute_query(query, (value, self.user_id))
            logging.info(f"Обновлён параметр {stat} до {value} для пользователя {self.user_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка обновления параметра {stat}: {e}")
            return False

    async def get_reputation(self):
        return self.stats.get('Reputation', 50)

    def add_buff(self, buff_name, duration, effect):
        """
        Добавление бафа/дебафа

        ИСПОЛЬЗОВАНИЕ:
        character.add_buff("Усиление атаки", 30, {"dmg": 1.5})
        """
        self.active_buffs.append({
            "name": buff_name,
            "duration": duration,
            "effect": effect
        })

    def remove_expired_buffs(self):
        """
        Удаление просроченных бафов
        """
        current_time = time.time()
        self.active_buffs = [
            buff for buff in self.active_buffs
            if buff['duration'] > current_time
        ]
