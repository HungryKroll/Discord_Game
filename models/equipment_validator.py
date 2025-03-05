import logging
from models.storage import StorageType
from config.database import fetch_query

class EquipmentValidator:
    @staticmethod
    async def can_equip(user_id, item):
        """
        Проверяет возможность экипировки предмета
        """
        if item['category'] == 'броня':
            return await EquipmentValidator._check_armor(user_id)
        if item['category'] == 'оружие':
            return await EquipmentValidator._check_weapons(user_id, item)
        if item['category'] == 'щит':
            return await EquipmentValidator._check_shield(user_id)
        return True

    @staticmethod
    async def _check_armor(user_id):
        """
        Проверяет, можно ли экипировать броню (разрешается только одна)
        """
        query = """
            SELECT COUNT(*) FROM equipment
            JOIN items ON equipment.item_id = items.id
            WHERE user_id = ? AND category = 'броня'
        """
        result = await fetch_query(query, (user_id,))
        return result[0][0] == 0

    @staticmethod
    async def _check_weapons(user_id, new_weapon):
        """
        Проверяет, можно ли экипировать оружие с учётом занятых слотов
        """
        query = """
            SELECT SUM(hand_slot) FROM equipment
            JOIN items ON equipment.item_id = items.id
            WHERE user_id = ? AND category IN ('оружие', 'щит')
        """
        result = await fetch_query(query, (user_id,))
        hands_used = result[0][0] or 0
        return (hands_used + new_weapon['hand_slot']) <= 2

    @staticmethod
    async def _check_shield(user_id):
        """
        Проверяет, можно ли экипировать щит (не более одного в руке)
        """
        query = """
            SELECT SUM(hand_slot) FROM equipment
            JOIN items ON equipment.item_id = items.id
            WHERE user_id = ? AND category IN ('оружие', 'щит')
        """
        result = await fetch_query(query, (user_id,))
        hands_used = result[0][0] or 0
        return hands_used < 2
