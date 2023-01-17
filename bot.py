import asyncio
import logging

import discord

import bot_config
import bot_logging
import bot_utils
import bot_musicplayer

instances = []

global log
log: logging.Logger = None


async def join(self, message, channel, loop):
    author = message.author
    if author.voice:
        if message.guild.voice_client in self.voice_clients:
            return
        if channel not in self.voice_clients:
            await channel.connect(self_deaf=True)
            instances.append(bot_musicplayer.MusicPlayer(channel.guild.voice_client, message.channel, loop))


async def leave(message):
    if message.guild.voice_client:
        for obj in instances:
            if obj.client == message.guild.voice_client:
                obj.destroy()
                instances.remove(obj)
                del obj
                break
        await message.guild.voice_client.disconnect()


class Client(discord.Client):
    async def on_ready(self):
        log.info('Logged on as \"%s\"', self.user)
        await self.change_presence(activity=discord.Game(name=bot_config.lang_cfg['activity']))

    async def on_message(self, message: discord.Message):
        author = message.author
        if author.voice is None:
            return
        channel = author.voice.channel
        if author == self.user:
            return
        message.guild.voice_client
        cf = bot_utils.CommandFormer(message.content)

        if cf.starts('play') or \
                cf.starts('q') or \
                cf.starts('paly'):
            await join(self, message, channel, asyncio.get_running_loop())
            if cf.equal('play') or cf.equal('q') or cf.equal('paly'):
                return
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    if cf.starts('play'):
                        await obj.queue(cf.get_args("play "))
                    if cf.starts('q'):
                        await obj.queue(cf.get_args("q "))
                    if cf.starts('paly'):
                        await obj.queue(cf.get_args("paly "))
                    break

        elif cf.starts('join'):
            await join(self, message, channel, asyncio.get_running_loop())
        elif cf.starts('leave'):
            await leave(message)
        elif cf.starts('pause') or cf.starts('stop'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    await obj.pause(True)
        elif cf.starts('resume'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    await obj.pause(False)
        elif cf.starts('skip'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    await obj.skip()
        elif cf.starts('loop'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    await obj.loop()
        elif cf.starts('np'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    song = obj.songs[obj.position]
                    await reply(message.channel, 'np', song.title + ', Position: ' + obj.position)
        elif cf.starts('clear'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    obj.songs.clear()
                    await reply(message.channel, 'clear')
                    log.info("\"%s\": Cleared playlist!", message.guild.name)
        elif cf.starts('rm') or cf.starts('remove'):
            split = message.content.split(' ')
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    song = obj.songs[int(split[1])]
                    obj.songs.remove(song)
                    await reply(message.channel, 'rm', song.title)
                    log.info("\"%s\": Removed %s", message.guild.name, song.title)
        elif cf.starts('shuffle'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    if obj.shuffle:
                        obj.shuffle = False
                        await reply(message.channel, 'shuffle', False)
                        log.info("\"%s\": Shuffle %s", message.guild.name, False)
                    else:
                        obj.shuffle = True
                        await reply(message.channel, 'shuffle', True)
                        log.info("\"%s\": Shuffle %s", message.guild.name, True)
        elif cf.starts('settings'):
            for obj in instances:
                if obj.client == message.guild.voice_client:
                    await reply(message.channel, 'settings', len(obj.songs), obj.shuffle, obj.loopMode, obj.position)
        # if message.content.startswith(prefix + 'help'):
        #    await reply(message.channel, 'help')
        del cf


async def reply(channel, cmd, *args):
    if bot_config.verbose:
        result = bot_config.lang_cfg[cmd]
        if args is not None:
            result = result % args
        return await channel.send(content=result)


if __name__ == '__main__':
    bot_logging.setup_logging()
    log = bot_logging.getLogger("bot_main")
    log.info('Starting MP')
    bot_config.load_config()
    log.info('Configs initialized. Version %s', bot_config.version)

    intents = discord.Intents.default()
    intents.message_content = True
    client = Client(intents=intents)
    client.run(bot_config.token, log_handler=None)
