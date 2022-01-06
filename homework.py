import logging
import json as simplejson

from dotenv import load_dotenv

import os
from http import HTTPStatus
import requests
import telegram
import time
from requests.exceptions import (ConnectionError,
                                 RequestException, TooManyRedirects)
from telegram import TelegramError
from CustomError import (ListHomeworkEmptyError, HomeworkVerdictError,
                        HomeworkNameError)
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

RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': 0}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(message, bot):
    """Отправляет сообщение в Telegram чат о статусе проверенной работы."""
    logging.info(f'Сообщение: {message}')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramError:
        logging.error("Ошибка отправки сообщения")


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_status = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
        logger.debug(f'Получен код API: {homework_status.status_code}')
        if homework_status.status_code != HTTPStatus.OK:
            raise Exception("Неверный ответ")
        logging.debug(f'Код API: {homework_status.status_code}')
        return homework_status.json()
    except simplejson.errors.JSONDecodeError:
        logging.error(
            f'Ответ не преобразовался в json : {homework_status.json()}')
    except ConnectionError:
        logging.error('Ошибка сервера')
    except RequestException as e:
        raise SystemExit(e)
    except TooManyRedirects:
        logging.error('Превышено количество перенаправлений')
        return {}


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homework = response['homeworks']
        if response['homeworks'] == []:
            return{}
    except KeyError:
        logger.error("Ключа homeworks нет в словаре.")
        raise SystemExit
    except TypeError as e:
        logger.error("Некоректный формат списка.")
        raise SystemExit(e)
    except ListHomeworkEmptyError:
        logger.error("Список работ пуст.")
        raise SystemExit
    if not isinstance (response, dict):
        raise TypeError("Некоректный формат словаря")
    if type(response['homeworks']) is not list:
        raise TypeError("Некоректный формат списка!")
    if not homework:
        raise ListHomeworkEmptyError("Список работ пуст!")
    else:
        return homework


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        message = 'Ответ не является словарем!'
        logger.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'Ключа homeworks нет в словаре.'
        logger.error(message)
        raise KeyError(message)

    if type(response['homeworks']) is not list:
        message = 'Домашние работы не являются списком!'
        logger.error(message)
        raise TypeError(message)

    if not response['homeworks']:
        message = 'Список работ пуст!'
        logger.error(message)
        raise ListHomeworkEmptyError(message)

    else:
        return response['homeworks']



def parse_status(homework):
    """Достаем статус работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
       
    except KeyError:
        logging.error(f'Ошибка с ключем в словаре {HOMEWORK_STATUSES}')
    except HomeworkNameError:
        logging.error("Произошла ошибка.")
    except HomeworkVerdictError:
        logging.info(f"Вердикт {HOMEWORK_STATUSES[homework['status']]}")
    if homework['homework_name'] is None:
        raise HomeworkNameError("Нет названия домашней работы!")
    if verdict is None:
        raise HomeworkVerdictError("Нет вердикта!")
    else:
        return (f'Изменился статус проверки работы "{homework_name}".'
                f'{verdict}')


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN is None or len(PRACTICUM_TOKEN) == 0:
        return False
    elif TELEGRAM_TOKEN is None or len(TELEGRAM_TOKEN) == 0:
        return False
    elif TELEGRAM_CHAT_ID is None or len(str(TELEGRAM_CHAT_ID)) == 0:
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот работает!')
    current_timestamp = int(0)
    while check_tokens():
        try:
            response = get_api_answer(current_timestamp)
            if check_response(response):
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
