from aiogram.filters.state import State, StatesGroup


class Setter(StatesGroup):
    # Состояние ввода имени сервиса
    entering_service_name = State()
    # Состояние ввода логина
    entering_login = State()
    # Состояние ввода пароля
    entering_password = State()
    # Состояние проверки введенных ответов
    on_review = State()
