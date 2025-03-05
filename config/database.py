# config\database.py
# Этот файл централизует работу с базой данных
# Содержит функции для выполнения запросов и получения данных
# Использует aiosqlite для асинхронной работы с SQLite

import aiosqlite
import logging

DATABASE_NAME = "game.db"

async def get_db():
    """
    Создает и возвращает подключение к базе данных

    ИСПОЛЬЗОВАНИЕ:
    db = await get_db()
    async with db.execute("SELECT * FROM table") as cursor:
        results = await cursor.fetchall()
    """
    try:
        db_connection = await aiosqlite.connect(DATABASE_NAME)
        logging.info("✅ Успешное подключение к базе данных.")
        return db_connection
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к базе данных: {e}")
        return None

async def execute_query(query, params=()):
    """
    Выполняет запросы на изменение данных

    ИСПОЛЬЗОВАНИЕ:
    result = await execute_query(
        "INSERT INTO characters (name) VALUES (?)",
        ("Player",)
    )
    """
    db = await get_db()

    if db is None:
        logging.error("Не удалось получить подключение к базе данных")
        return False

    try:
        await db.execute("BEGIN TRANSACTION")  # Начало транзакции
        await db.execute(query, params)
        await db.commit()
        logging.info(f"Запрос выполнен: {query} с параметрами {params}")
        return True

    except Exception as e:
        await db.rollback()
        logging.error(f"❌ Ошибка при выполнении запроса: {query}. Ошибка: {e}")
        return False

    finally:
        await db.close()

async def fetch_query(query, params=()):
    """
    Получает данные из базы данных

    ИСПОЛЬЗОВАНИЕ:
    results = await fetch_query(
        "SELECT * FROM characters WHERE id = ?",
        (user_id,)
    )
    """
    db = await get_db()
    if db is None:
        logging.error("Не удалось получить подключение к базе данных")
        return []
    try:
        async with db.execute(query, params) as cursor:
            results = await cursor.fetchall()
            logging.info(f"Запрос выполнен: {query}")
            return results
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
        return []

async def close_db():
    """
    Закрывает соединение с базой данных

    ИСПОЛЬЗОВАНИЕ:
    await close_db()
    """
    try:
        db = await get_db()
        if db:
            await db.close()
            logging.info("✅ Соединение с базой данных закрыто.")
            # Дополнительно можно добавить обнуление соединения
            db = None
    except Exception as e:
        logging.error(f"❌ Ошибка при закрытии базы данных: {e}")

async def init_database():
    """
    Инициализация базы данных и создание необходимых таблиц

    ИСПОЛЬЗОВАНИЕ:
    await init_database()
    """
    try:
        db = await get_db()
        if db is None:
            logging.error("Не удалось получить подключение к базе данных")
            return False
        await db.commit()
        logging.info("✅ База данных инициализирована успешно")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации базы данных: {e}")
        return False
