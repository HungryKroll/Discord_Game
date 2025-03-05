# models\inventory.py

from models.storage import StorageType
from typing import Optional
from config.database import fetch_query, execute_query
from config.logger import safe_execute
from models.item import Item
import logging


class InventoryManager:
    GOLD_ITEM_ID = 1  # ID золота в таблице items

    @staticmethod
    @safe_execute
    async def get_items(user_id: int, storage: StorageType):
        """Получение предметов из указанного хранилища"""
        query = f"""
            SELECT items.*, {storage.value['storage']}.quantity 
            FROM {storage.value['storage']}
            JOIN items ON {storage.value['storage']}.item_id = items.id
            WHERE user_id = ?
        """

        if not results:
            return []
        else:
            results = await fetch_query(query, (user_id,))

        return [dict(zip(ITEM_FIELDS + ['quantity'], row)) for row in results]

    @staticmethod
    @safe_execute
    async def add_item(
            user_id: int,
            item_id: int,
            quantity: int,
            storage: StorageType,
    ) -> bool:
        """
        Добавление предмета в хранилище
        """
        if not isinstance(storage, StorageType):
            raise ValueError("Недопустимый тип хранилища")

        query = f"""
            INSERT INTO {storage.value['storage']} (user_id, item_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET 
            quantity = {storage.value['storage']}.quantity + excluded.quantity
        """

        logging.info(f"Игроку {user_id} дабвлено {quantity} штуки {item_id} в {storage}")

        await execute_query(query, (user_id, item_id, quantity))
        return True

    @staticmethod
    @safe_execute
    async def remove_item(
            user_id: int,
            item_id: int,
            quantity: int,
            storage: StorageType
    ) -> bool:
        """
        Удаление предмета из хранилища
        """

        current = await fetch_query(
            f"SELECT quantity FROM {storage.value['storage']} WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
        current = current[0][0] if current else 0  # Проверяем, есть ли данные

        if current < quantity:
            return False  # Если предметов меньше, чем надо удалить

        new_quantity = current - quantity

        if new_quantity > 0:
            await execute_query(
                f"UPDATE {storage.value['storage']} SET quantity = ? WHERE user_id = ? AND item_id = ?",
                (new_quantity, user_id, item_id)
            )
        else:
            await execute_query(
                f"DELETE FROM {storage.value['storage']} WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            )

        logging.info(f"У игрока {user_id} удалено {quantity} штуки {item_id} из {storage}")
        return True

    @staticmethod
    @safe_execute
    async def move_item(
            user_id: int,
            item_id: int,
            quantity: int,
            from_storage: StorageType,
            to_storage: StorageType
    ) -> bool:
        from models.equipment_validator import EquipmentValidator

        """Перемещает предмет между хранилищами с транзакцией."""
        # Проверка категории для снаряжения
        if to_storage == StorageType.EQUIPMENT:
            item = await Item.get_item_by_id(item_id)
            if not item:
                logging.error(f"Предмет {item_id} не найден.")
                return False

            if not StorageType.check_category(to_storage, item['category']):
                logging.warning(f"Предмет {item['name']} нельзя экипировать.")
                return False

            if not await EquipmentValidator.can_equip(user_id, item):
                return False

        # Транзакция
        try:
            # Удаление из исходного хранилища
            if not await InventoryManager.remove_item(user_id, item_id, quantity, from_storage):
                return False

            # Добавление в целевое хранилище
            return await InventoryManager.add_item(user_id, item_id, quantity, to_storage)

        except Exception as e:
            logging.error(f"Ошибка перемещения: {e}")
            return False

    @staticmethod
    @safe_execute
    async def get_gold(user_id: int, storage: Optional[StorageType] = None) -> int:
        """Возвращает золото в указанном хранилище или общее."""
        if storage:
            query = f"SELECT quantity FROM {storage.value['storage']} WHERE user_id = ? AND item_id = ?"
            result = await fetch_query(query, (user_id, InventoryManager.GOLD_ITEM_ID))
            return result[0][0] if result else 0
        else:
            return await InventoryManager.get_gold(user_id, StorageType.INVENTORY) + \
                await InventoryManager.get_gold(user_id, StorageType.EQUIPMENT)

    @staticmethod
    @safe_execute
    async def spend_gold(
            user_id: int,
            amount: int,
            only_equipment: bool = False
    ) -> dict:
        """Списывает золото с учетом приоритета (снаряжение → инвентарь)."""
        report = {"spent_equipment": 0, "spent_inventory": 0, "success": False}

        # Золото в снаряжении
        equipment_gold = await fetch_query(
            "SELECT quantity FROM equipment WHERE user_id = ? AND item_id = ?",
            (user_id, InventoryManager.GOLD_ITEM_ID)
        )
        equipment_gold = equipment_gold[0][0] if equipment_gold else 0

        if only_equipment:
            if equipment_gold >= amount:
                await execute_query(
                    "UPDATE equipment SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
                    (amount, user_id, InventoryManager.GOLD_ITEM_ID)
                )
                report["spent_equipment"] = amount
                report["success"] = True
            return report

        # Списание из снаряжения
        if equipment_gold > 0:
            spent = min(equipment_gold, amount)
            await execute_query(
                "UPDATE equipment SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
                (spent, user_id, InventoryManager.GOLD_ITEM_ID)
            )
            report["spent_equipment"] = spent
            amount -= spent

        # Списание из инвентаря
        if amount > 0:
            inventory_gold = await fetch_query(
                "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, InventoryManager.GOLD_ITEM_ID)
            )
            inventory_gold = inventory_gold[0][0] if inventory_gold else 0

            if inventory_gold >= amount:
                await execute_query(
                    "UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
                    (amount, user_id, InventoryManager.GOLD_ITEM_ID)
                )
                report["spent_inventory"] = amount
                report["success"] = True
            else:
                # Откат частичного списания из снаряжения
                if report["spent_equipment"] > 0:
                    await execute_query(
                        "UPDATE equipment SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?",
                        (report["spent_equipment"], user_id, InventoryManager.GOLD_ITEM_ID)
                    )
                report["success"] = False

        return report

    @staticmethod
    @safe_execute
    async def sell_item(
            user_id: int,
            item_id: int,
            quantity: int,
            storage: StorageType
    ) -> bool:
        """Продажа предмета с транзакцией."""
        try:
            # Удаление предмета
            if not await InventoryManager.remove_item(user_id, item_id, quantity, storage):
                return False

            # Начисление золота
            item = await Item.get_item_by_id(item_id)
            character = await Character.get_from_db(user_id)
            total_price = Item.calculate_price(item, quantity, await character.get_reputation())

            return await InventoryManager.add_item(
                user_id,
                InventoryManager.GOLD_ITEM_ID,
                total_price,
                StorageType.INVENTORY
            )

        except Exception as e:
            logging.error(f"Ошибка продажи: {e}")
            return False
