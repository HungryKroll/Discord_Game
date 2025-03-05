# config\session_manager.py
import aiohttp
import logging
import asyncio

class SessionManager:
    _instance = None
    _session = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_session(cls):
        async with cls._lock:
            if cls._session is None or cls._session.closed:
                try:
                    cls._session = aiohttp.ClientSession()
                    logging.info("✅ Создана новая aiohttp сессия")
                except Exception as e:
                    logging.error(f"❌ Ошибка создания сессии: {e}")
                    return None
            return cls._session

    @classmethod
    async def close_session(cls):
        async with cls._lock:
            if cls._session and not cls._session.closed:
                try:
                    await cls._session.close()
                    logging.info("✅ aiohttp сессия закрыта")
                except Exception as e:
                    logging.error(f"❌ Ошибка закрытия сессии: {e}")
                finally:
                    cls._session = None


    @classmethod
    async def make_request(
        cls,
        url,
        method='GET',
        params=None,
        headers=None,
        json=None,
        timeout=30
    ):
        """
        Универсальный метод для выполнения HTTP-запросов

        ИСПОЛЬЗОВАНИЕ:
        response = await SessionManager().make_request(
            'https://api.example.com/data',
            params={'key': 'value'}
        )
        """
        session = await cls.get_session()
        if not session:
            logging.error("Не удалось получить сессию")
            return None

        try:
            async with session.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                logging.info(f"Запрос {method} {url}: {response.status}")

                if response.status == 200:
                    return await response.json()
                else:
                    logging.warning(f"Ошибка запроса: {response.status}")
                    return None

        except aiohttp.ClientError as e:
            logging.error(f"Ошибка сети: {e}")
            return None
        except asyncio.TimeoutError:
            logging.error("Превышено время ожидания запроса")
            return None

    async def __aenter__(self):
        """Поддержка асинхронного контекстного менеджера"""
        return await self.get_session()

    async def __aexit__(self, exc_type, exc, tb):
        """Закрытие сессии при выходе из контекста"""
        await self.close_session()
