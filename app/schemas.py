from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

#Схемы для TodoList

class TodoListBase(BaseModel):
    name: str = Field(..., example="Мои задачи")  # Название списка дел

class TodoListCreate(TodoListBase):
    pass  # Для создания список дел, ничего не добавляем

class TodoListUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Обновленное имя")  # Можно обновить имя

class TodoListInDB(TodoListBase):
    id: int  # ID из базы
    deleted_at: Optional[datetime]  # Дата мягкого удаления или None
    completed_count: int  # Кол-во выполненных задач
    total_count: int  # Общее кол-во задач
    progress: float = Field(..., example=75.0)  # Процент выполненных (только в API)
    
    class Config:
        orm_mode = True  # Позволяет работать с ORM объектами напрямую


# --- Схемы для Item ---

class ItemBase(BaseModel):
    name: str = Field(..., example="Купить молоко")
    text: str = Field(..., example="Пойти в магазин и купить молоко")
    is_done: bool = Field(False, example=False)

class ItemCreate(ItemBase):
    pass  # Для создания

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Обновленное название")
    text: Optional[str] = Field(None, example="Обновленный текст")
    is_done: Optional[bool] = Field(None, example=True)

class ItemInDB(ItemBase):
    id: int
    todo_list_id: int
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True
