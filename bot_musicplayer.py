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

ads_enabled = None
ads_chance = None
YDL_OPTIONS = None
FFMPEG_OPTIONS = None
project_dir = None


global log
log = getLogger('bot_player')


class Song:
    sourceUrl = None
    title = None
    url = None
    id = None
    playlist_title = None

    def __init__(self, source_url, title, url, video_id, playlist_title=None):
        self.sourceUrl = source_url
        self.title = title
        self.url = url
        self.id = video_id
        self.playlist_title = playlist_title


class MusicPlayer:
    client: discord.VoiceClient = None
    guild: discord.Guild = None
    textChannel: discord.TextChannel = None
    eventLoop = None
    adPlayed = False
    shuffle = False
    stop = False
    playing = False
    position = 0
    loopMode = 0
    songs = []

    def __init__(self, voice_client, text_channel, loop):
        global ads_chance, ads_enabled, YDL_OPTIONS, FFMPEG_OPTIONS, project_dir
        self.client = voice_client
        self.guild = text_channel.guild
        self.textChannel = text_channel
        self.eventLoop = loop

        ads_enabled = bot_config.ads_enabled
        ads_chance = bot_config.ads_chance
        YDL_OPTIONS = bot_config.YDL_OPTIONS
        FFMPEG_OPTIONS = bot_config.FFMPEG_OPTIONS
        project_dir = bot_config.project_dir

        log.info("New Instance opened at \"" + text_channel.guild.name + "\"")

    async def music(self):
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
        source = await discord.FFmpegOpusAudio.from_probe(self.songs[self.position].sourceUrl, **FFMPEG_OPTIONS)
        self.client.play(source, after=lambda e: asyncio.run(self.song_complete()))
        log.info("\"%s\": Playing position %s: %s %s",
                 self.guild.name,
                 str(self.position),
                 self.songs[self.position].url,
                 str(self.songs[self.position].title))

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

        async def async_queue(music):
            global load_msg
            await load_msg.delete()
            if music:
                await reply(self.textChannel, 'play', result.url)
                await self.music()

        asyncio.run_coroutine_threadsafe(load_message(), self.eventLoop)

        try:
            if message.startswith('https://') and not message.count('playlist'):
                if message.count('&list'):
                    message = message.split('&list')[0]
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(message, download=False)
                    url = 'https://youtu.be/' + info['id']
                    result = Song(info.get("url"), info.get("title"), url, info.get("id"))
                    self.songs.append(result)
                    log.info("\"%s\": Request \"%s\" took %ds!", self.guild.name,
                             result.title,
                             time.time() - startTime)

            elif message.startswith('https://') and message.count('playlist'):
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(message, download=False)
                    entries = info['entries']
                    for data in entries:
                        try:
                            url = message
                            result = Song(data.get("url"), data['title'], url, data['id'], info.get("title"))
                            self.songs.append(result)
                        except:
                            continue

                    log.info("\"%s\": Request \"%s\" took %ds!", self.guild.name,
                             result.playlist_title,
                             time.time() - startTime)
            else:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(("ytsearch:" + message), download=False)
                    data = info['entries'][0]
                    url = 'https://youtu.be/' + data['id']
                    result = Song(data['url'], data['title'], url, data['id'])
                    self.songs.append(result)
                    log.info("\"%s\": Request \"%s\" took %ds!", self.guild.name,
                             result.title,
                             time.time() - startTime)
        except Exception as e:
            log.error("Something messed up within the extractor.")
            log.error(e)
            asyncio.run_coroutine_threadsafe(async_queue(False), self.eventLoop)
            return

        asyncio.run_coroutine_threadsafe(async_queue(True), self.eventLoop)

    def destroy(self):
        log.info("Instance closed at \"" + self.guild.name + "\"")
        self.stop = True
        self.songs.clear()
