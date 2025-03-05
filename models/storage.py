# models\storage.py
from enum import Enum


class StorageType(Enum):
    """
    Типы хранилищ с дополнительными атрибутами.
    Используем Enum для безопасности типов и удобства.
    """

    INVENTORY = {
        "display": "🎒 Инвентарь",
        "storage": "inventory",
        "allowed_categories": None  # Все категории разрешены
    }

    EQUIPMENT = {
        "display": "🔧 Снаряжение",
        "storage": "equipment",
        "allowed_categories": None  # Все категории разрешены
    }

    @classmethod
    def get_by_name(cls, name: str):
        """Получить тип хранилища по имени"""
        try:
            return cls[name.upper()]
        except KeyError:
            logging.warning(f"Неизвестный тип хранилища: {name}")
            return None

    @classmethod
    def check_category(cls, storage_type, category: str) -> bool:
        """Проверка, разрешена ли категория для хранилища"""
        if storage_type not in cls:
            return False

        # Для инвентаря разрешены все категории
        if storage_type.value["allowed_categories"] is None:
            return True

        return category in storage_type.value["allowed_categories"]

    def get_storage_name(self):
        return self.value["storage"]
