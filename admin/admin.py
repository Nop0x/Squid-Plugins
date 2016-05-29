import discord
from discord.ext import commands
from cogs.utils import checks
from __main__ import settings
import asyncio
import logging


log = logging.getLogger("red.admin")


class Admin:
    """Admin tools, more to come."""

    def __init__(self, bot):
        self.bot = bot
        self._announce_msg = None

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def addrole(self, ctx, rolename, user: discord.Member=None):
        author = ctx.message.author
        channel = ctx.message.channel
        server = ctx.message.server
        role = discord.utils.find(lambda r: r.name.lower() == rolename.lower(),
                                  ctx.message.server.roles)
        if user is None:
            user = author

        if role is None:
            await self.bot.say('That role cannot be found.')
            return

        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say('I don\'t have manage_roles.')
            return

        if author.id == settings.owner:
            pass
        elif not channel.permissions_for(author).manage_roles:
            raise commands.CheckFailure

        await self.bot.add_roles(user, role)
        await self.bot.say('Added role {} to {}'.format(role.name, user.name))

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def announce(self, ctx, *, msg):
        """Announces a message to all servers that a bot is in."""
        if self._announce_msg is not None:
            await self.bot.say("Already announcing, wait until complete to"
                               " issue a new announcement.")
        else:
            self._announce_msg = msg

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def removerole(self, ctx, rolename, user: discord.Member=None):
        pass

    @commands.command(no_pm=True, pass_context=True)
    async def say(self, ctx, *, text):
        """Repeats what you tell it.

        Can use `message`, `channel`, `server`, and `discord`
        """
        try:
            evald = eval(text, {}, {'message': ctx.message,
                                    'channel': ctx.message.channel,
                                    'server': ctx.message.server,
                                    'discord': discord})
        except:
            evald = text
        if len(str(evald)) > 2000:
            evald = str(evald)[:1990] + " you fuck."
        await self.bot.say(evald)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def sudo(self, ctx, user: discord.Member, *, command):
        """Runs the [command] as if [user] had run it. DON'T ADD A PREFIX
        """
        new_msg = deepcopy(ctx.message)
        new_msg.author = user
        new_msg.content = self.bot.command_prefix[0] + command
        await self.bot.process_commands(new_msg)

    async def announcer(self, msg):
        server_ids = map(lambda s: s.id, self.bot.servers)
        for server_id in server_ids:
            server = self.bot.get_server(server_id)
            if server is None:
                continue
            chan = server.default_channel
            log.debug("Looking to announce to {} on {}".format(chan.name,
                                                               server.name))
            me = server.me
            if chan.permissions_for(me).send_messages:
                log.debug("I can send messages to {} on {}, sending".format(
                    server.name, chan.name))
                await self.bot.send_message(chan, msg)
            await asyncio.sleep(1)

    async def announce_manager(self):
        while self == self.bot.get_cog('Admin'):
            if self._announce_msg is not None:
                log.debug("Found new announce message, announcing")
                await self.announcer(self._announce_msg)
                self._announce_msg = None
            await asyncio.sleep(1)


def setup(bot):
    n = Admin(bot)
    bot.add_cog(n)
    bot.loop.create_task(n.announce_manager())
