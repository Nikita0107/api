from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_tables, delete_tables
from router import router as router_doc


# Декоратор для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()  # Создаем таблицы в базе данных
    print('Таблицы созданы')
    yield
    await delete_tables()  # Удаляем таблицы из базы данных
    print('Таблицы удалены')

# Создаем экземпляр FastAPI с указанным жизненным циклом и настройками документации
app = FastAPI(
    title="Nika",
    description="Апи сохраняет картинку в БД и на локальный сервер. Извлекает текс с картинки в БД. Удаляет по id записи с БД и картинку с сервера!",
    version="1.0.0",
    lifespan=lifespan
)

# Добавляем роутер
app.include_router(router_doc)


