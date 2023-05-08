import asyncio
import re
import emoji

import config
import bot_answers

from setter import Setter

from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from aiogram.utils.keyboard import InlineKeyboardBuilder


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


# Универсальный обработчик ввода пользователя
async def universal_handler(user_message: Message,
                            state, next_state: FSMContext,
                            data_name: str,
                            bot_message_text: str | None = None) -> None:
    user_answer = user_message.text
    data = await state.get_data()
    answers = data['answers']
    # Проверим ответ пользователя на соответствие шаблону
    if re.match(r"^[^'\"“”„`«»\n]+$", user_answer) is not None:
        answers[data_name] = user_answer
        await state.update_data(answers=answers)
        # Отправим следующий запрос, если он есть
        if bot_message_text is not None:
            bot_message = await user_message.answer(bot_message_text)
            await add_delete_ids(state, bot_message)
        await state.set_state(next_state)
    # Отправим сообщение об ошибке ввода при несоответствии шаблону
    else:
        bot_message = await user_message.answer(bot_answers.input_err)
        await add_delete_ids(state, bot_message)

    await add_delete_ids(state, user_message)


# Функция обработки и показа введенных ответов
async def review_answers(bot: Bot, message: Message, state: FSMContext) -> None:
    await delete_temp_messages(bot, state, message.chat.id)
    data = await state.get_data()
    answers = data['answers']
    output = 'Данные о сервисе:\n\n'

    keyboard = InlineKeyboardBuilder()
    keyboard.button(callback_data='push_answers', text=bot_answers.send)

    for key, value in answers.items():
        output += emoji.emojize(':small_blue_diamond:') + f'{key}: {value}\n'

    bot_message = await message.answer(output, reply_markup=keyboard.as_markup())
    await add_delete_ids(state, bot_message)


async def autodelete_message(message: Message) -> None:
    await asyncio.sleep(config.hide_time)
    await message.delete()
