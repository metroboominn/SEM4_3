from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List
from datetime import datetime

from app import models, schemas, database

router = APIRouter()

#CRUD для TodoList

@router.post("/todo_lists/", response_model=schemas.TodoListInDB, status_code=status.HTTP_201_CREATED)
async def create_todo_list(todo_list: schemas.TodoListCreate, db: AsyncSession = Depends(database.get_async_session)):
    new_todo = models.TodoList(
        name=todo_list.name,
        completed_count=0,
        total_count=0,
        deleted_at=None
    )
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return await enrich_todo_progress(new_todo, db)


@router.get("/todo_lists/", response_model=List[schemas.TodoListInDB])
async def read_todo_lists(db: AsyncSession = Depends(database.get_async_session)):
    # Получаем только не удалённые todo_lists
    result = await db.execute(select(models.TodoList).where(models.TodoList.deleted_at.is_(None)))
    todo_lists = result.scalars().all()

    enriched = []
    for todo in todo_lists:
        enriched.append(await enrich_todo_progress(todo, db))
    return enriched


@router.get("/todo_lists/{todo_id}", response_model=schemas.TodoListInDB)
async def read_todo_list(todo_id: int, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.TodoList).where(models.TodoList.id == todo_id, models.TodoList.deleted_at.is_(None))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TodoList not found")
    return await enrich_todo_progress(todo, db)


@router.patch("/todo_lists/{todo_id}", response_model=schemas.TodoListInDB)
async def update_todo_list(todo_id: int, todo_update: schemas.TodoListUpdate, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.TodoList).where(models.TodoList.id == todo_id, models.TodoList.deleted_at.is_(None))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TodoList not found")

    if todo_update.name is not None:
        todo.name = todo_update.name

    await db.commit()
    await db.refresh(todo)
    return await enrich_todo_progress(todo, db)


@router.delete("/todo_lists/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_list(todo_id: int, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.TodoList).where(models.TodoList.id == todo_id, models.TodoList.deleted_at.is_(None))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TodoList not found")

    todo.deleted_at = datetime.utcnow()  # Мягкое удаление
    await db.commit()
    return None


#CRUD для Item

@router.post("/todo_lists/{todo_id}/items/", response_model=schemas.ItemInDB, status_code=status.HTTP_201_CREATED)
async def create_item(todo_id: int, item: schemas.ItemCreate, db: AsyncSession = Depends(database.get_async_session)):
    # Проверяем что список дел существует и не удалён
    result = await db.execute(
        select(models.TodoList).where(models.TodoList.id == todo_id, models.TodoList.deleted_at.is_(None))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TodoList not found")

    new_item = models.Item(
        todo_list_id=todo_id,
        name=item.name,
        text=item.text,
        is_done=item.is_done,
        deleted_at=None
    )
    db.add(new_item)

    # Обновляем счетчики в TodoList
    todo.total_count += 1
    if new_item.is_done:
        todo.completed_count += 1

    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.get("/todo_lists/{todo_id}/items/", response_model=List[schemas.ItemInDB])
async def read_items(todo_id: int, db: AsyncSession = Depends(database.get_async_session)):
    # Проверяем что список дел существует и не удалён
    result = await db.execute(
        select(models.TodoList).where(models.TodoList.id == todo_id, models.TodoList.deleted_at.is_(None))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TodoList not found")

    result = await db.execute(
        select(models.Item).where(
            models.Item.todo_list_id == todo_id,
            models.Item.deleted_at.is_(None)
        )
    )
    items = result.scalars().all()
    return items


@router.get("/items/{item_id}", response_model=schemas.ItemInDB)
async def read_item(item_id: int, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.Item).where(models.Item.id == item_id, models.Item.deleted_at.is_(None))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}", response_model=schemas.ItemInDB)
async def update_item(item_id: int, item_update: schemas.ItemUpdate, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.Item).where(models.Item.id == item_id, models.Item.deleted_at.is_(None))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    old_is_done = item.is_done

    if item_update.name is not None:
        item.name = item_update.name
    if item_update.text is not None:
        item.text = item_update.text
    if item_update.is_done is not None:
        item.is_done = item_update.is_done

    # Если изменился статус is_done, обновляем счетчики в связанный TodoList
    if old_is_done != item.is_done:
        todo = await db.get(models.TodoList, item.todo_list_id)
        if todo and todo.deleted_at is None:
            if item.is_done:
                todo.completed_count += 1
            else:
                todo.completed_count -= 1

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: AsyncSession = Depends(database.get_async_session)):
    result = await db.execute(
        select(models.Item).where(models.Item.id == item_id, models.Item.deleted_at.is_(None))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.deleted_at = datetime.utcnow()  # Мягкое удаление

    # Обновляем счетчики у связанного TodoList
    todo = await db.get(models.TodoList, item.todo_list_id)
    if todo and todo.deleted_at is None:
        todo.total_count -= 1
        if item.is_done:
            todo.completed_count -= 1

    await db.commit()
    return None


# --- Вспомогательная функция для вычисления progress ---

async def enrich_todo_progress(todo: models.TodoList, db: AsyncSession) -> schemas.TodoListInDB:
    # Вычисляем прогресс в процентах
    progress = 0.0
    if todo.total_count > 0:
        progress = (todo.completed_count / todo.total_count) * 100

    # Создаем объект схемы для ответа, с прогрессом
    todo_data = schemas.TodoListInDB.from_orm(todo)
    todo_data.progress = round(progress, 2)
    return todo_data
