import logging.handlers

import discord


def setup_logging():
    logging.basicConfig(
        handlers=[logging.handlers.RotatingFileHandler(filename="logs/ve_output.log", maxBytes=512000, backupCount=4)],
        level=logging.DEBUG,
        format='%(levelname)s %(asctime)s %(message)s',
        datefmt='%m/%d/%Y%I:%M:%S %p')
    discord.utils.setup_logging()

def getLogger(name):
    return logging.getLogger(name)
