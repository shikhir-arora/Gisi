import logging
import os
import sys
import traceback
from datetime import datetime
from os import path

from aiohttp import ClientSession
from discord import AsyncWebhookAdapter, Embed, Webhook
from discord.ext.commands import AutoShardedBot, CommandInvokeError

from .config import Config
from .constants import FileLocations
from .core import Core
from .utils import WebDriver
from . import utils

log = logging.getLogger(__name__)


class Gisi(AutoShardedBot):

    def __init__(self):
        self.config = Config.load()
        super().__init__(self.config.command_prefix, self_bot=True)

        self.aiosession = ClientSession()
        self.webdriver = WebDriver(kill_on_exit=False)
        self.webhook = Webhook.from_url(self.config.webhook_url, adapter=AsyncWebhookAdapter(
            self.aiosession)) if self.config.webhook_url else None

        self.add_cog(Core(self))

        self.load_exts()
        log.info("Gisi setup!")

    def __str__(self):
        return "<Gisi>"

    def load_exts(self):
        for extension in os.listdir(FileLocations.COGS):
            if extension.endswith(".py"):
                ext_name = extension[:-3]
                ext_package = f"{__package__}.cogs.{ext_name}"
                try:
                    self.load_extension(ext_package)
                except Exception:
                    log.exception(f"Couldn't load extension. ({ext_name})")
                else:
                    log.debug(f"loaded extension {ext_name}")
        log.info(f"loaded {len(self.extensions)} extensions")

    async def run(self):
        await self.login(self.config.token, bot=False)
        try:
            await self.connect()
        finally:
            self.dispatch("shutdown")

    async def on_ready(self):
        await self.webdriver.spawn()
        log.info("ready!")

    async def on_shutdown(self):
        self.aiosession.close()
        self.webdriver.close()

    async def on_error(self, event_method, *args, **kwargs):
        log.exception("Client error")
        if self.webhook:
            args = "\n".join([f"{arg}" for arg in args])
            kwargs = "\n".join([f"{key}: {value}" for key, value in kwargs.items()])
            ctx_em = Embed(title="Context Info", timestamp=datetime.now(), colour=0xFFE389,
                           description=f"event: **{event_method}**\nArgs:```\n{args}```\nKwargs:```\n{kwargs}```")

            exc_em = utils.embed.create_exception_embed(*sys.exc_info(), 8)
            await self.webhook.send(embeds=[ctx_em, exc_em])

    async def on_command_error(self, context, exception):
        log.error(f"Command error {context} / {exception}")
        if self.webhook:
            ctx_em = Embed(title="Context Info", timestamp=datetime.now(), colour=0xFFE389,
                           description=f"cog: **{type(context.cog).__qualname__}**\nguild: **{context.guild}**\nchannel: **{context.channel}**\nauthor: **{context.author}**")
            ctx_em.add_field(name="Message",
                             value=f"id: **{context.message.id}**\ncontent:```\n{context.message.content}```",
                             inline=False)
            args = "\n".join([f"{arg}" for arg in context.args])
            kwargs = "\n".join([f"{key}: {value}" for key, value in context.kwargs.items()])
            ctx_em.add_field(name="Command",
                             value=f"name: **{context.command.name}**\nArgs:```\n{args}```\nKwargs:```\n{kwargs}```",
                             inline=False)

            if isinstance(exception, CommandInvokeError):
                exc_type = type(exception.original)
                exc_msg = str(exception.original)
                exc_tb = exception.original.__traceback__
            else:
                exc_type = type(exception)
                exc_msg = str(exception)
                exc_tb = exception.__traceback__

            exc_em = utils.embed.create_exception_embed(exc_type, exc_msg, exc_tb, 8)
            await self.webhook.send(embeds=[ctx_em, exc_em])
