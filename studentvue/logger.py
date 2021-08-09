import logging
import sys
import os

logger = logging.getLogger()


class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


def initLogger(debug=False, logfile=None, loglevel=None):
    # redirect messages to either stdout or stderr based on loglevel
    # stdout < logging.WARNING <= stderr
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(module)s]: %(message)s')
    logging_out = logging.StreamHandler(sys.stdout)
    logging_err = logging.StreamHandler(sys.stderr)
    logging_out.setFormatter(formatter)
    logging_err.setFormatter(formatter)
    logging_out.addFilter(MaxLevelFilter(logging.WARNING))
    logging_out.setLevel(logging.DEBUG)
    logging_err.setLevel(logging.WARNING)

    # root logger, no __name__ as in submodules further down the hierarchy
    global logger
    logger.addHandler(logging_out)
    logger.addHandler(logging_err)
    if logfile is not None:
        if not os.path.isabs(logfile):
            logfile = f'{os.path.abspath(os.path.dirname(sys.argv[0]))}/{logfile}'
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        logging_file = logging.FileHandler(logfile)
        logging_file.setFormatter(formatter)
        if loglevel is not None:
            logging_file.setLevel(loglevel)
        else:
            logging_file.setLevel(logging.INFO)
        logger.addHandler(logging_file)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info("----------------------------------------------------------------------")
    logger.info("Logging initialized from " + __name__)


# Expose logger methods
info = logger.info
error = logger.error
debug = logger.debug
warning = logger.warning
exception = logger.exception
