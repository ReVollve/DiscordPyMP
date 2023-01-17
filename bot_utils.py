import asyncio
import functools
import typing

import bot_config


class CommandFormer:
    message: str = None
    prefix = None

    def starts(self, key):
        return self.message.startswith(self.prefix + key)

    def equal(self, key):
        return self.message == self.prefix + key

    def get_args(self, key):
        return self.message.replace(self.prefix + key, "")

    def __init__(self, message):
        self.message = message
        self.prefix = bot_config.prefix


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
