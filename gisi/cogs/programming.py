import json
import logging
import re
import textwrap
import traceback

from discord import Embed
from discord.ext.commands import command

from gisi.constants import Colours
from gisi.utils import github, text_utils

log = logging.getLogger(__name__)


class Programming:
    """Programming for the cool kids"""

    def __init__(self, bot):
        self.bot = bot
        self.aiosession = bot.aiosession

    @command(usage="<instructions>")
    async def eval(self, ctx):
        """A simple eval command which evaluates the given instructions.

        To be honest it actually executes them but uhm... bite me!
        """
        inst = textwrap.indent(ctx.clean_content, "\t")
        statement = f"out = []\ndef print(*args):\n\tout.append(\" \".join(str(arg) for arg in args))\nasync def func():\n{inst}"
        env = {**globals(), **locals()}

        em = Embed(
            title="Parsing",
            description=text_utils.code(ctx.clean_content, "python"),
            colour=0xffff80
        )
        await ctx.message.edit(content="", embed=em)

        try:
            exec(statement, env)
        except SyntaxError as e:
            em.colour = Colours.ERROR
            em.add_field(
                name="Syntax Error",
                value="".join(traceback.format_exception_only(type(e), e))
            )
            log.exception("Here's the detailed syntax error:")
            await ctx.message.edit(embed=em)
            return
        func = env["func"]

        em.title = "Executing..."
        em.colour = 0xff9900
        await ctx.message.edit(embed=em)

        try:
            ret = await func()
            out = env["out"]
        except BaseException as e:
            em.colour = Colours.ERROR
            em.add_field(
                name="Error",
                value="".join(traceback.format_exception_only(type(e), e))
            )
            log.exception("Here's the detailed syntax error:")
            await ctx.message.edit(embed=em)
            return

        em.title = "Done"
        em.colour = Colours.SUCCESS
        if str(ret):
            try:
                raw_result = json.dumps(ret, cls=BeautyFormatter, indent=2)
                result = text_utils.code(raw_result, "json")
            except TypeError:
                raw_result = result = str(ret)
            if len(result) > 1024:
                gist = await github.create_gist(self.aiosession, f"Result for:\n{ctx.clean_content}",
                                                {"result.json": raw_result})
                em.url = gist.html_url
                result = f"The result is too big. [Here's a link to a Gist]({gist.html_url})"
            em.add_field(
                name="Result",
                value=result
            )
        if out:
            result = "\n".join(out)
            if len(result) > 1024:
                gist = await github.create_gist(self.aiosession, f"Console output for:\n{ctx.clean_content}",
                                                {"output.txt": result})
                result = f"The Output is too big. [Here's a link to a Gist]({gist.html_url})"
            em.add_field(
                name="Output",
                value=result
            )

        await ctx.message.edit(embed=em)


def setup(bot):
    bot.add_cog(Programming(bot))


class BeautyFormatter(json.JSONEncoder):
    MASK = 8 * "*"
    VALUES_RE = re.compile(r"^(?:\d[ -]*?){13,16}$")
    KEYS = frozenset([
        "password",
        "secret",
        "passwd",
        "authorization",
        "api_key",
        "apikey",
        "sentry_dsn",
        "access_token",
        "token",
        "webhook_url",
        "mongodb_uri"
    ])

    def stringify(self, item, value):
        value = str(value)
        if not item:
            return value

        if isinstance(item, bytes):
            item = item.decode("utf-8", "replace")
        else:
            item = str(item)

        item = item.lower()
        for key in self.KEYS:
            if key in item:
                # store mask as a fixed length for security
                return self.MASK

        if isinstance(value, str) and self.VALUES_RE.match(value):
            return self.MASK
        return value

    def default(self, o, key=None, n=0, visited=None):
        if n > 1:
            return self.stringify(key, o)
        visited = visited or []
        if o in visited:
            return self.stringify(key, o)

        visited.append(o)
        try:
            if isinstance(o, dict):
                d = o
            else:
                d = vars(o)
        except Exception:
            return self.stringify(key, o)
        else:
            obj = {}
            for key, value in d.items():
                if not key.startswith("__"):
                    try:
                        value = self.default(value, key=key, n=n + 1, visited=visited)
                    except Exception:
                        value = self.stringify(key, value)
                else:
                    value = self.stringify(key, value)
                visited.append(value)
                obj[key] = value
            return obj
