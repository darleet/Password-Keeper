import re

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import bot_answers
import database_service
from handlers.reseters import add_delete_ids


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


# Универсальный обработчик кнопок
async def universal_button(message: Message, state: FSMContext, action: str) -> None:
    await message.answer(bot_answers.get_command)
    user_services = await database_service.functions.list_services(message.from_user.id)

    # Если нет ни одного записанного сервиса
    if user_services is None:
        await message.answer(bot_answers.no_data_warning)
    else:
        keyboard = InlineKeyboardBuilder()
        for service in user_services:
            keyboard.button(callback_data=f'service_{action}_{service}', text=service)
        keyboard.adjust(1, repeat=True)
        bot_message = await message.answer('Выберите сервис', reply_markup=keyboard.as_markup())
        await add_delete_ids(state, bot_message)
