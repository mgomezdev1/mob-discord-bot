from discord.ext import commands
import logging
import discord

logger = logging.Logger(__name__)

class TestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Inititalized Test Cog")

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Just a silly ping-pong time
        """
        await ctx.channel.send("pong!")

    @commands.command()
    async def amimuted(self, ctx: commands.Context):
        """
        Ever wondering if you're muted in VC? Let me check!
        """
        channels = ctx.guild.channels
        for c in channels:
            if c.type != discord.ChannelType.voice:
                continue
            for m in c.members:
                if m.id != ctx.author.id:
                    continue
                muted = m.voice.mute or m.voice.self_mute or m.voice.suppress
                await ctx.reply(f"You are{' not ' if not muted else ' '}muted!")
                return
        await ctx.reply(f"I can't find you in a voice channel :(")

async def setup(bot: commands.Bot):
    await bot.add_cog(TestCog(bot))