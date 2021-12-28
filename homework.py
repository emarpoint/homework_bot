import logging

from dotenv import load_dotenv

import os

import requests
import telegram
import time
from requests.exceptions import (
    ConnectionError)

load_dotenv()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log',
    filemode='a')


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': 0}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(message, bot):
    """ Отправляет сообщение в Telegram чат"""
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    current_timestamp = current_timestamp or int(0)
    params = {'from_date': current_timestamp}
    try:
        homework_status = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
        logger.debug(f'Получен код API: {homework_status.status_code}')
        if homework_status.status_code != 200:
            raise Exception("Неверный ответ")
        logging.info(f'Код API: {homework_status.status_code}')
        return homework_status.json()
    except ConnectionError:
        print("Ошибка сервера!")
        return {}


def check_response(response):
    homeworks = response['homeworks']

    if homeworks is None:
        logger.error("Нет домашней работы")
        raise Exception("Нет домашней работы")
    if type(homeworks) is not list:
        logger.error("Некоректный формат списка")
        raise Exception("Некоректный формат списка")
    if not homeworks:
        logger.debug("Список работ пуст.")
        raise Exception("Список работ пуст.")
    return homeworks


def parse_status(homework):
    """Достаем статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework.get('status')]
    if homework_name is None or homework_status is None:
        raise Exception("Произошла ошибка")
    if verdict is None:
        raise Exception("Нет вердикта")
    logging.info(f'Вердикт {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    def practicum_token():
        if PRACTICUM_TOKEN is None or len(PRACTICUM_TOKEN) == 0:
            return False
        else:
            return True

    def telegram_token():
        if TELEGRAM_TOKEN is None and len(TELEGRAM_TOKEN) == 0:
            return False
        else:
            return True

    def telegram_chat_id():
        if TELEGRAM_CHAT_ID is None and len(TELEGRAM_CHAT_ID) == 0:
            return False
        else:
            return True
    if all([practicum_token() and telegram_token()
            and telegram_chat_id()]) is True:
        return True
    else:
        logger.critical(
            'Отсутствует обязательная переменная окружения.'
            'Программа принудительно остановлена.')
    return False


def main():
    """Основная логика работы бота."""
    logger = logging.getLogger(__name__)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот работает!')
    current_timestamp = int(0)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if check_tokens() is False:
                message = 'Произошла ошибка в check_tokens'
                send_message(message, bot)
            elif check_response(response):
                logger.info(response.get('homeworks')[0])
                send_message(
                    parse_status(response.get('homeworks')[0]),
                    bot)
            current_timestamp = response.get('current_date',
                                             current_timestamp)
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.exception(f'Бот столкнулся с ошибкой: {error}')
            message = f'Произошла ошибка программы: {error}'
            send_message(message, bot)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
