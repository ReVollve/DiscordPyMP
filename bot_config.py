import json
import os

import bot_logging

log = bot_logging.getLogger("bot_config")

bot_cfg: dict
lang_cfg: dict

version: str = None
lang: str = None
token: str = None
prefix: str = None
verbose: bool = None
ads_enabled: bool = None
ads_chance: int = None
FFMPEG_OPTIONS: dict = None
YDL_OPTIONS: dict = None
project_dir = os.path.dirname(__file__)


def load_config():
    try:
        global bot_cfg, lang_cfg
        bot_json = open('bot.json', encoding='utf-8')
        bot_cfg = json.load(bot_json)
        __verify_integrity_bot()

        lang_json = open("lang/" + lang + ".json", encoding='utf-8')
        lang_cfg = json.load(lang_json)
        __verify_integrity_lang()

    except Exception as e:
        log.critical("An critical error appeared during the config setup!")
        log.critical(e)
        exit(-1)


def __verify_integrity_bot():
    global version, lang, token, prefix, verbose, ads_enabled, ads_chance, FFMPEG_OPTIONS, YDL_OPTIONS

    version = bot_cfg['sVersion']
    lang = bot_cfg['sLang']
    token = bot_cfg['sToken']
    prefix = bot_cfg['sPrefix']
    verbose = bot_cfg['bVerbose']
    ads_enabled = bot_cfg['bAdsEnabled']
    ads_chance = bot_cfg['nAdsChance']
    FFMPEG_OPTIONS = bot_cfg['FFMPEG_OPTIONS']
    YDL_OPTIONS = bot_cfg['YDL_OPTIONS']


def __verify_integrity_lang():
    lang_cfg['play']
    lang_cfg['stop']
    lang_cfg['resume']
    lang_cfg['jump']
    lang_cfg['skip']
    lang_cfg['np']
    lang_cfg['activity']
    lang_cfg['loopq']
    lang_cfg['noloop']
    lang_cfg['looptrack']
    lang_cfg['clear']
    lang_cfg['load']
    lang_cfg['settings']
    lang_cfg['shuffle']
    lang_cfg['rm']
