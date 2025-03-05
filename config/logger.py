# config\logger.py
# КОММЕНТАРИЙ:
# Этот файл настраивает систему логирования
# Добавляем обёртку safe_execute для безопасного выполнения функций
# Позволяет логировать время выполнения и ошибки

import os
import logging
import sys
import time
import traceback
from functools import wraps
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Настраивает логирование с расширенной конфигурацией

    ИСПОЛЬЗОВАНИЕ:
    from config.logger import setup_logger
    setup_logger()
    """
    # Создаем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Общий уровень логирования

    # Очистим существующие обработчики, если они есть
    logger.handlers.clear()

    # Форматирование лога
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Создание директории для логов
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Настройка консольного обработчика
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Уровень логирования для консоли
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Настройка файлового обработчика с ротацией
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bot.log'),
        encoding='utf-8',
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Уровень логирования для файла
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def safe_execute(func):
    """
    Декоратор для безопасного выполнения асинхронных функций с логированием
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):  # Добавлены *args и **kwargs
        try:
            start = time.time()
            result = await func(*args, **kwargs)  # Передача аргументов
            logging.info(f"✅ {func.__name__} выполнена за {time.time()-start:.2f} сек")
            return result
        except Exception as e:
            logging.error(f"❌ Ошибка в {func.__name__}: {str(e)}")
            return None
    return wrapper

