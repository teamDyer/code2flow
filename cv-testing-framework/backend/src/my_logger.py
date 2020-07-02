import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('scraper.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - '
    '%(filename)s - '
    '%(funcName)s - '
    '%(lineno)s - '
    '%(levelname)s - '
    '%(message)s')
handler.setFormatter(formatter)

# add the file handler to the logger
logger.addHandler(handler)
