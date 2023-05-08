import emoji
import config


start_answer = 'Здравствуйте!\n\nСо мной Ваши логины и пароли от сервисов будут в целости и сохранности, ' \
               'дело за малым - напишите их мне, а я их спрячу в надежное место!\n\n' \
               'Используйте следующие команды:\n' + \
               emoji.emojize(':black_small_square:') + ' /set - добавить логин и пароль к сервису\n' + \
               emoji.emojize(':black_small_square:') + ' /get - получить логин и пароль по названию сервиса\n' + \
               emoji.emojize(':black_small_square:') + ' /del - удалить логин и пароль для сервиса'

set_command = emoji.emojize(':pencil:') + ' *Добавление нового сервиса*'
input_err = emoji.emojize(':cross_mark:') + ' Не допускается использовать кавычки или несколько строк ' \
                                           'для ввода данных. Повторите ввод!'

rewrite_warning = 'У Вас уже есть запись для этого сервиса. Хотите ее перезаписать?'
data_loading = f'{emoji.emojize(":incoming_envelope:")} Данные загружаются...'
data_sent = f'{emoji.emojize(":closed_mailbox_with_raised_flag:")} Данные отправлены!'
operation_cancelled = f'{emoji.emojize(":wastebasket:")} Операция отменена.'

send = f'Отправить {emoji.emojize(":check_mark_button:")}'
rewrite = f'{emoji.emojize(":check_mark_button:")} Перезаписать'
cancel = f'{emoji.emojize(":cross_mark:")} Отменить'

get_command = emoji.emojize(':floppy_disk:') + ' *Получение данных о сервисе*'
no_data_warning = emoji.emojize(':warning:') + ' Не найдено записей'


def print_service(service_name, service_login, service_pass):
    return f'*Данные для сервиса {service_name}*\n' \
           f'Логин: {service_login}\n' \
           f'Пароль: {service_pass}'


hide_warning = f'Пароль будет скрыт через {config.hide_time} секунд'
