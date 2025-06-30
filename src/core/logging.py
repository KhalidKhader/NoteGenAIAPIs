import logging
import colorlog
import os
environment = os.getenv('PY_ENV', 'development')


# setup loggers
# logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

if (environment == 'production'):
    # Create a logger
    logger = logging.getLogger('notegenaiapis')
    logger.setLevel(logging.DEBUG)

    # Create a StreamHandler with a custom formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)
else:
    # Create a custom log level-to-color mapping
    log_colors = {
        'DEBUG': 'green',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }

    # Create a logger
    logger = logging.getLogger('notegenaiapis')
    logger.setLevel(logging.DEBUG)

    # Create a StreamHandler with a custom formatter
    handler = logging.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s  call_trace=%(pathname)s L%(lineno)-4d',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors=log_colors
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)