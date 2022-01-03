# # example_for_log.py

# import logging

# from logging.handlers import RotatingFileHandler

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     filename='main.log',
#     filemode='a')

# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# handler = RotatingFileHandler(
#     'my_logger.log', maxBytes=50000000, backupCount=5)
# handler.setFormatter(formatter)

# logger.addHandler(handler)

# logger.debug('123')
# logger.info('Сообщение отправлено')
# logger.warning('Большая нагрузка!')
# logger.error('Бот не смог отправить сообщение')
# logger.critical('Всё упало! Зовите админа!1!111')
