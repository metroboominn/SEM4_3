from fastapi import FastAPI
from app.routes import router  # Импортируем маршруты из app.routes

app = FastAPI()  # Создаем объект приложения FastAPI

app.include_router(router)  # Подключаем маршруты к приложению
