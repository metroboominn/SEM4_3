import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env

DATABASE_URL = os.getenv("DATABASE_URL")  # Получаем полный URL подключения из переменных окружения

# Создаем асинхронный движок SQLAlchemy с этим URL
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем асинхронную сессию для работы с базой данных
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Асинхронный генератор для получения сессии
async def get_async_session():
    async with async_session() as session:
        yield session
