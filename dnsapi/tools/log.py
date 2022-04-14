# -*- coding:utf-8 -*-
'''日志模块'''
import os
import uuid
import logging
from logging.handlers import RotatingFileHandler

LOG_POOL = {}

def getLogger(filename="", logFileLevel=logging.INFO, consoleLevel=logging.INFO):
    '''获取日志对象'''
    if filename:
        logfilename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log', filename)
        if LOG_POOL.has_key(logfilename):
            return LOG_POOL[logfilename]
        logger = logging.getLogger(logfilename)
    else:
        logger = logging.getLogger(str(uuid.uuid4()))
    level = consoleLevel if consoleLevel < logFileLevel or not filename else logFileLevel
    logger.setLevel(level=level)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')

    console = logging.StreamHandler()
    console.setLevel(consoleLevel)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if filename:
        rHandler = RotatingFileHandler(logfilename, maxBytes=1*1024*1024, backupCount=10)
        rHandler.setLevel(logFileLevel)
        rHandler.setFormatter(formatter)
        logger.addHandler(rHandler)
        LOG_POOL[logfilename] = logger

    return logger
