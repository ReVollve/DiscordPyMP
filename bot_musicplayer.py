import asyncio
import os
import random
import time

import discord
import yt_dlp

from bot import reply
from bot_logging import getLogger
import bot_config
from bot_utils import to_thread

ads_enabled = bot_config.ads_enabled
ads_chance = bot_config.ads_chance
YDL_OPTIONS = bot_config.YDL_OPTIONS
FFMPEG_OPTIONS = bot_config.FFMPEG_OPTIONS
project_dir = bot_config.project_dir

global log
log = getLogger('bot_player')


class Song:
    source_url = None
    title = None
    url = None
    id = None
    origin_title = None

    def __init__(self, source_url, title, url, video_id, origin_title):
        self.source_url = source_url
        self.title = title
        self.url = url
        self.id = video_id
        self.origin_title = origin_title


class MusicPlayer:
    client: discord.VoiceClient = None
    guild: discord.Guild = None
    textChannel: discord.TextChannel = None
    eventLoop = None
    guild_name = None
    adPlayed = False
    shuffle = False
    stop = False
    playing = False
    position = 0
    loopMode = 0
    songs = []

    def __init__(self, voice_client, text_channel, loop):
        self.client = voice_client
        self.guild = text_channel.guild
        self.textChannel = text_channel
        self.eventLoop = loop
        self.guild_name = self.guild.name

        log.info("New Instance opened at \"" + text_channel.guild.name + "\"")

    async def music(self):
        cache = self.position
        size = len(self.songs)
        if size == 0:
            log.info("\"" + self.guild.name + "\": Playlist empty")
            return
        if self.playing:
            return
        if self.position >= size:
            log.warning("\"" + self.guild.name + "\": Something messed up: position >= size: " + str(
                self.position) + ' >= ' + str(size))
            return
        self.playing = True
        try:
            source = await discord.FFmpegOpusAudio.from_probe(self.songs[self.position].source_url, **FFMPEG_OPTIONS)
            self.client.play(source, after=lambda e: asyncio.run(self.song_complete()))
            log.info("\"%s\": Playing position %s: %s %s",
                     self.guild.name,
                     str(self.position),
                     self.songs[self.position].url,
                     str(self.songs[self.position].title))
        except Exception as e:
            log.warning("\"%s\": An error occurred during playing position %d. Skipping and removing song from queue",
                        self.guild.name, self.position)
            if bot_config.debug:
                log.warning(e.with_traceback())
            self.adPlayed = True
            self.songs.pop(cache)

    async def song_complete(self):
        self.playing = False
        if self.stop:
            return
        if ads_enabled:
            if not self.adPlayed:
                chance = random.randint(0, int(ads_chance))
                if chance == 1:
                    file = random.choice(os.listdir(project_dir + "/ads"))
                    path = os.path.abspath("ads/" + file)
                    log.info("\"%s\": Playing ad: %s", self.guild.name, file)
                    self.client.play(discord.FFmpegPCMAudio(path), after=lambda e: asyncio.run(self.song_complete()))
                    self.adPlayed = True
                    return
        self.adPlayed = False
        if self.shuffle:
            self.position = random.randint(0, len(self.songs) - 1)
            await self.music()
            return
        if self.loopMode == 0:
            self.position += 1
        if self.loopMode == 1:
            size = len(self.songs)
            if self.position + 1 == size:
                self.position = 0
            else:
                self.position += 1
        await self.music()

    async def skip(self):
        self.client.pause()
        self.playing = False
        if self.shuffle:
            self.position = random.randint(0, len(self.songs) - 1)
            await self.music()
            return
        if self.loopMode == 1:
            size = len(self.songs)
            if self.position + 1 == size:
                self.position = 0
            else:
                self.position += 1
        else:
            self.position += 1
        await self.music()

    def pause(self, val):
        if val:
            self.client.pause()
        else:
            self.client.resume()

    async def loop(self):
        if self.loopMode == 0:  # normal
            self.loopMode = 1
            log.info("\"%s\": Changed looping mode to loop queue (1) ", self.guild.name)
            await reply(self.textChannel, 'loopq')
        elif self.loopMode == 1:  # loop queue
            self.loopMode = 2
            log.info("\"%s\": Changed looping mode to loop track (2) ", self.guild.name)
            await reply(self.textChannel, 'looptrack')
        elif self.loopMode == 2:  # loop track
            self.loopMode = 0
            log.info("\"%s\": Changed looping mode to no loop (0) ", self.guild.name)
            await reply(self.textChannel, 'noloop')

    @to_thread
    def queue(self, message):
        log.info("\"%s\": Request \"%s\"", self.guild.name, message)

        startTime = time.time()

        load_msg: discord.Message = None

        async def load_message():
            global load_msg
            load_msg = await reply(self.textChannel, 'load')

        async def delete_message():
            global load_msg
            await load_msg.delete()

        async def start_music():
            await reply(self.textChannel, 'play', result.url)
            await self.music()

        asyncio.run_coroutine_threadsafe(load_message(), self.eventLoop)

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                https = message.startswith('https://')
                playlist = message.count('playlist')
                hasList = message.count('&list')

                global info
                info = None
                global result
                result = None

                if https and not playlist:
                    if hasList:
                        info = ydl.extract_info(message.split('&list')[0], download=False)
                    else:
                        info = ydl.extract_info(message, download=False)
                elif https and playlist:
                    info = ydl.extract_info(message, download=False)
                else:
                    info = ydl.extract_info(("ytsearch:" + message), download=False)
                    info = info['entries'][0]
                if playlist:
                    entries = info['entries']
                    for elem in entries:
                        try:
                            url = message
                            result = Song(elem.get("url"), elem['title'], url, elem['id'], info.get("title"))
                            self.songs.append(result)
                        except:
                            continue
                else:
                    url = 'https://youtu.be/' + info['id']
                    result = Song(info.get("url"), info.get("title"), url, info.get("id"), info.get("title"))
                    self.songs.append(result)

                log.info("\"%s\": Request \"%s\" took %ds!", self.guild.name,
                         result.origin_title,
                         time.time() - startTime)


        except Exception as e:
            log.error("Something messed up within the extractor.")
            if bot_config.debug:
                log.error(e.with_traceback())
            asyncio.run_coroutine_threadsafe(delete_message(), self.eventLoop)
            return

        asyncio.run_coroutine_threadsafe(delete_message(), self.eventLoop)
        asyncio.run_coroutine_threadsafe(start_music(), self.eventLoop)

    def destroy(self):
        log.info("Instance closed at \"" + self.guild.name + "\"")
        self.stop = True
        self.songs.clear()
