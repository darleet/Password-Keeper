import asyncio
import os

import asyncpg


# Функция подключения к базе данных
async def connect_db() -> asyncpg.Connection:
    retries = 0
    while retries < 5:
        try:
            conn = await asyncpg.connect(os.getenv('DATABASE'))
            return conn
        except asyncpg.ConnectionFailureError:
            await asyncio.sleep(5)
            retries += 1
    raise asyncpg.ConnectionFailureError


# Функция создания таблицы для нового пользователя
async def add_user(user_id: int) -> None:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {str_user_id} (
                    service_name TEXT PRIMARY KEY,
                    login TEXT,
                    password TEXT
                );
            ''')
    await conn.close()


# Функция добавления сервиса с логином и паролем
async def add_service(user_id: int, service_name, login, password: str) -> None:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    try:
        await conn.execute(f'INSERT INTO {str_user_id} (service_name, login, password) '
                           f'VALUES ($1, $2, $3)', service_name, login, password)
    # Если пользователя еще нет в БД, добавим таблицу для него и снова попробуем записать данные
    except asyncpg.UndefinedTableError:
        await add_user(user_id)
        await add_service(user_id, service_name, login, password)
    finally:
        await conn.close()


# Функция перезаписи сервера в базе данных
async def rewrite_service(user_id: int, service_name, login, password: str) -> None:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    await conn.execute(f'UPDATE {str_user_id} '
                       f'SET login = $1, password = $2 '
                       f'WHERE service_name = $3',
                       login, password, service_name)
    await conn.close()


# Функция показа всех сервисов пользователя
async def list_services(user_id: int) -> list | None:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    try:
        rows = await conn.fetch(f'SELECT (service_name) FROM {str_user_id}')
        services = [row[0] for row in rows]
        return services
    # Если пользователя еще нет в БД, добавим таблицу для него
    except asyncpg.UndefinedTableError:
        await add_user(user_id)
    finally:
        await conn.close()


# Функция получения логина и пароля от сервиса
async def get_service(user_id: int, service_name: str) -> tuple[str, str]:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    service = await conn.fetchrow(f'SELECT * FROM {str_user_id} '
                                  f'WHERE service_name = $1', service_name)
    await conn.close()
    return service['login'], service['password']


# Функция удаления сервиса из базы данных
async def del_service(user_id: int, service_name: str) -> None:
    conn = await connect_db()
    str_user_id = f'id{user_id}'
    await conn.execute(f'DELETE FROM {str_user_id} WHERE service_name = $1', service_name)
    await conn.close()

