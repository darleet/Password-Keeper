import asyncio
import os

from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


# Функция ресета временных данных пользователей
async def reset_data(state: FSMContext) -> None:
    await state.set_state()
    await state.update_data(delete_ids=[], answers=dict())


# Функция добавления id сообщения для его последующего удаления
async def add_delete_ids(state: FSMContext, *messages: Message) -> None:
    for message in messages:
        data = await state.get_data()
        delete_ids = data['delete_ids']
        delete_ids.append(message.message_id)
        await state.update_data(delete_ids=delete_ids)


# Функция удаления сообщений, помеченных к удалению
async def delete_temp_messages(bot: Bot, state: FSMContext, chat_id: int) -> None:
    data = await state.get_data()
    delete_ids = data['delete_ids']
    for message_id in delete_ids:
        await bot.delete_message(chat_id, message_id)
    await state.update_data(delete_ids=[])


async def autodelete_message(message: Message) -> None:
    await asyncio.sleep(int(os.getenv('HIDE_TIME')))
    await message.delete()
