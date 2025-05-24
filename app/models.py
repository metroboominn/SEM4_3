from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # Создаем базовый класс моделей

class TodoList(Base):
    __tablename__ = "todo_lists"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный ID списка дел
    name = Column(String, index=True, nullable=False)  # Название списка дел
    completed_count = Column(Integer, default=0)       # Количество выполненных задач
    total_count = Column(Integer, default=0)           # Общее количество задач
    deleted_at = Column(DateTime, nullable=True)       # Мягкое удаление: время удаления или NULL

    items = relationship("Item", back_populates="todo_list", cascade="all, delete-orphan")
    # Связь с элементами списка дел

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный ID элемента
    todo_list_id = Column(Integer, ForeignKey("todo_lists.id"), nullable=False)  # Внешний ключ на список дел
    name = Column(String, nullable=False)              # Название задачи
    text = Column(String, nullable=False)              # Текст/описание задачи
    is_done = Column(Boolean, default=False)           # Статус выполнения
    deleted_at = Column(DateTime, nullable=True)       # Мягкое удаление

    todo_list = relationship("TodoList", back_populates="items")
    # Связь с родительским списком дел
