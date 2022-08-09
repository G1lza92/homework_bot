from email import message
import logging
import os
import time
from http import HTTPStatus
from urllib import response

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    filename='errors.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)

def send_message(bot, message):
    """Отправка сообщений в Телеграм"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправленно в чат.')
    except Exception as error:
        message = f'Не отправляются сообщения, {error}'
        logger.error(message)
        raise SystemError(message)


def get_api_answer(current_timestamp):
    """Запрашиваем статус домашней работы"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        message = f'Ошибка получения request, {error}'
        logger.error(message)
        raise SystemError(message)
    if response.status_code != HTTPStatus.OK:
        message = f'Ошибка запроса к API, {response.status_code}'
        logger.error(message)
        raise SystemError(message)
    else:
        logger.info('Эндпоинт получен')
        response = response.json()
    return response

def check_response(response):
    """Проверяем корректность API"""
    try:
        homeworks_list = response['homeworks']
    except KeyError as error:
        message = f'Ошибка по ключу homeworks {error}'
        logger.error(message)
        raise KeyError(message)
    if len(homeworks_list) == 0:
        message = f'Домашних работ нет'
        logger.error(message)
        raise SystemError(message)
    if homeworks_list is None:
        message = f'В ответе API нет словаря homeworks'
        logger.error(message)
        raise SystemError(message)
    if not isinstance(homeworks_list, list):
        message = 'Домашняя работа приходит не в виде списка в ответ от API'
        logger.error(message)
        raise TypeError(message)
    return homeworks_list


def parse_status(homework):
    """Парсинг инфо о домашней работе"""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as error:
        message = f'Ошибка по ключу homework_name {error}'
        logger.error(message)
        raise KeyError(message)
    try:
        homework_status = homework.get('status')
    except KeyError as error:
        message = f'Ошибка по ключу status {error}'
        logger.error(message)
        raise KeyError(message)

    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        message = f'Неизвестный статус домашней работы'
        logger.error(message)
        raise SystemError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности обязательных переменных окружения"""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота"""
    if not check_tokens():
        logger.critical(f'отсутствие обязательных переменных окружения')
        raise SystemExit('Остановка программы')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    homework_status = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            last_hmwrk_status = homeworks[0].get('status')
            if last_hmwrk_status != homework_status:
                homework_status = last_hmwrk_status
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('Обновления статуса нет')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
