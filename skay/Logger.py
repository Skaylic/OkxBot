import logging


def setup_logger():
    """
    Использую logging
    чтобы при деплое легко переключить сохранение логов в файл
    :return:
    """
    log_Format = "%(asctime)s: %(levelname).3s | (%(filename)s): %(funcName)s (%(lineno)d) | %(message)s"
    logging.basicConfig(
        filename='applogs.log',
        datefmt='%y-%m-%d %H:%M:%S',
        format=log_Format,
        encoding='utf-8'
    )
    cons = logging.StreamHandler()
    logger = logging.getLogger('SkayBot')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(cons)
    return logger
