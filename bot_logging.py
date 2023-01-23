import logging.handlers

import discord

import bot_config


def setup_logging():
    debug = bot_config.debug
    if debug:
        logging.basicConfig(
            handlers=[
                logging.handlers.RotatingFileHandler(filename="logs/bot.log", maxBytes=512000, backupCount=4)],
            level=logging.DEBUG,
            format='%(levelname)s %(asctime)s %(message)s',
            datefmt='%m/%d/%Y%I:%M:%S %p')
    else:
        logging.basicConfig(
            handlers=[logging.handlers.RotatingFileHandler(filename="logs/bot.log", maxBytes=512000, backupCount=4)],
            level=logging.INFO,
            format='%(levelname)s %(asctime)s %(message)s',
            datefmt='%m/%d/%Y%I:%M:%S %p')
    discord.utils.setup_logging()


def getLogger(name):
    return logging.getLogger(name)
