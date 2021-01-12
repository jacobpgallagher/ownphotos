import os
import logging
import logging.handlers

logger = logging.getLogger('image_similarity')
fomatter = logging.Formatter(
            '%(asctime)s : %(filename)s : %(funcName)s : %(lineno)s : %(levelname)s : %(message)s')
fileMaxByte = 256 * 1024 * 200  # 100MB
fileHandler = logging.handlers.RotatingFileHandler(
            '{}/image_similarity.log'.format(os.environ.get('LOG_DIR', 'logs')), maxBytes=fileMaxByte, backupCount=10)
fileHandler.setFormatter(fomatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.INFO)
