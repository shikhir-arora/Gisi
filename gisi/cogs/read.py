import discord
from discord.ext.commands import command
import logging

log = logging.getLogger(__name__)

class Read:
    """Marks stuff as read or something.
    """

    def __init__(self, bot):
        self.bot = bot

    @command()
    async def read(self, ctx, id: int=None):
        """Marks a specified server as read. If an ID is not provided, all servers will be marked as read."""
        await ctx.message.delete()
        if id:
            guild = self.bot.get_guild(int(id))
            if guild:
                await guild.ack()
                await ctx.send("Marked guild {} as read.".format(guild.name))
            else:
                await ctx.send("Invalid server ID.")
        else:
            for guild in self.bot.guilds:
                await guild.ack()
            await ctx.send("Marked all {} guilds as read.".format(len(self.bot.guilds)))

def setup(bot):
    bot.add_cog(Read(bot))
