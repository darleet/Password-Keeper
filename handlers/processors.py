import asyncpg
import emoji

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import bot_answers
import database_service
from handlers.reseters import delete_temp_messages, add_delete_ids, reset_data


# Функция обработки и показа введенных ответов
async def review_answers(bot: Bot, message: Message, state: FSMContext) -> None:
    await delete_temp_messages(bot, state, message.chat.id)
    data = await state.get_data()
    answers = data['answers']
    output = 'Данные о сервисе:\n\n'

    # Добавим кнопки
    keyboard = InlineKeyboardBuilder()
    keyboard.button(callback_data='push_answers', text=bot_answers.send)
    keyboard.button(callback_data='button_cancel', text=bot_answers.cancel)

    for key, value in answers.items():
        output += emoji.emojize(':small_blue_diamond:') + f'{key}: {value}\n'

    bot_message = await message.answer(output, reply_markup=keyboard.as_markup())
    await add_delete_ids(state, bot_message)


# Функция перезаписи ответов
async def rewrite_answers(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(bot_answers.data_loading)
    await callback_query.answer('Данные загружаются...')
    data = await state.get_data()
    answers = data['answers']
    try:
        await database_service.functions.add_service(
            callback_query.from_user.id,
            answers['Название'],
            answers['Логин'],
            answers['Пароль']
        )
        await callback_query.message.edit_text(bot_answers.data_sent)
        await callback_query.answer('Данные отправлены!')
        await reset_data(state)
    except asyncpg.UniqueViolationError:
        # Добавим кнопки
        keyboard = InlineKeyboardBuilder()
        keyboard.button(callback_data='rewrite_answers', text=bot_answers.rewrite)
        keyboard.button(callback_data='button_cancel', text=bot_answers.cancel)

        await callback_query.message.edit_text(bot_answers.rewrite_warning,
                                               reply_markup=keyboard.as_markup())
