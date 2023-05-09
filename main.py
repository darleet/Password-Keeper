import asyncio
import logging

import asyncpg

import config
import bot_answers

import db_connection
import handlers

from setter import Setter

from aiogram import Bot, Dispatcher, Router
from aiogram import filters

from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.storage.redis import RedisStorage
from redis import asyncio as aioredis

logging.basicConfig(level=logging.INFO)

# Подключимся к Редису для хранения FSM состояний в долговременной памяти
redis = aioredis.Redis.from_url(config.redis)
storage = RedisStorage(redis)

# Токен телеграм бота
token = config.token

# Создадим новый роутер
router = Router()

# Инициализируем бота и диспетчер
bot = Bot(token=token, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher(storage=storage)
dp.include_router(router)


# Обработчик команды /set
@router.message(filters.Command('set'))
async def set_handler(message: Message, state: FSMContext) -> None:
    await message.answer(bot_answers.set_command)
    await state.update_data(delete_ids=[], answers=dict())
    # Отправим просьбу ввести название сервиса
    bot_message = await message.answer('Введите название сервиса')
    await handlers.add_delete_ids(state, bot_message)
    await state.set_state(Setter.entering_service_name)


@router.message(filters.Command('cancel'))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    await message.answer(bot_answers.operation_cancelled)
    await handlers.delete_temp_messages(bot, state, message.chat.id)
    await handlers.reset_data(state)


# Обработчик ввода названия сервиса
@router.message(Setter.entering_service_name)
async def name_handler(message: Message, state: FSMContext) -> None:
    await handlers.universal_handler(message, state, Setter.entering_login, 'Название', 'Введите логин')


# Обработчик ввода логина
@router.message(Setter.entering_login)
async def login_handler(message: Message, state: FSMContext) -> None:
    await handlers.universal_handler(message, state, Setter.entering_password, 'Логин', 'Введите пароль')


# Обработчик ввода пароля
@router.message(Setter.entering_password)
async def password_handler(message: Message, state: FSMContext) -> None:
    await handlers.universal_handler(message, state, Setter.on_review, 'Пароль')
    if await state.get_state() == Setter.on_review:
        await handlers.review_answers(bot, message, state)


# Этот обработчик будет вызван в случае случайной отправки сообщения при подтверждении
@router.message(Setter.on_review)
async def review_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Для начала подтвердите или отмените отправку данных!')
    await handlers.review_answers(bot, message, state)


# Обработчик отправки сервиса в базу данных
@router.callback_query(filters.Text('push_answers'))
async def process_answers(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text(bot_answers.data_loading)
    await callback_query.answer('Данные загружаются...')
    data = await state.get_data()
    answers = data['answers']
    try:
        await db_connection.add_service(
            callback_query.from_user.id,
            answers['Название'],
            answers['Логин'],
            answers['Пароль']
        )
        await callback_query.message.edit_text(bot_answers.data_sent)
        await callback_query.answer('Данные отправлены!')
        await handlers.reset_data(state)
    except asyncpg.UniqueViolationError:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(callback_data='button_cancel', text=bot_answers.cancel)
        keyboard.button(callback_data='rewrite_answers', text=bot_answers.rewrite)

        await callback_query.message.edit_text(bot_answers.rewrite_warning,
                                               reply_markup=keyboard.as_markup())


# Обработчик перезаписи сервиса в базе данных
@router.callback_query(filters.Text('rewrite_answers'))
async def rewrite_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text(bot_answers.data_loading)
    await callback_query.answer('Данные загружаются...')
    data = await state.get_data()
    answers = data['answers']
    await db_connection.rewrite_service(
        callback_query.from_user.id,
        answers['Название'],
        answers['Логин'],
        answers['Пароль']
    )
    await callback_query.message.edit_text(bot_answers.data_sent)
    await callback_query.answer('Данные отправлены!')
    await handlers.reset_data(state)


# Обработчик кнопки "Отмена"
@router.callback_query(filters.Text('button_cancel'))
async def cancel_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text(bot_answers.operation_cancelled)
    await callback_query.answer('Операция отменена.')
    await handlers.reset_data(state)


# Обработчик команды /get
@router.message(filters.Command('get'))
async def set_handler(message: Message) -> None:
    await message.answer(bot_answers.get_command)
    user_services = await db_connection.list_services(message.from_user.id)

    # Если нет ни одного записанного сервиса
    if user_services is None:
        await message.answer(bot_answers.no_data_warning)
    else:
        keyboard = InlineKeyboardBuilder()
        for service in user_services:
            keyboard.button(callback_data=f'service_{service}', text=service)
        await message.answer('Выберите сервис', reply_markup=keyboard.as_markup())


# Обработчик кнопки с названием сервиса для получения его логина и пароля
@router.callback_query(filters.Text(startswith='service_'))
async def service_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()
    service_name = callback_query.data.split('_')[1]
    login, password = await db_connection.get_service(callback_query.from_user.id, service_name)
    bot_message = await callback_query.message.answer(bot_answers.print_service(service_name, login, password))
    await callback_query.answer(bot_answers.hide_warning)
    # Добавим автоудаление сообщения по истечении времени
    await handlers.autodelete_message(bot_message)


@router.message()
async def start_handler(message: Message) -> None:
    await message.answer(bot_answers.start_answer)


# Функция запуска бота
async def main() -> None:
    logging.info('Starting bot...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
