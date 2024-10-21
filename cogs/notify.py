import asyncio
from collections import defaultdict

import discord
from discord.ext import commands, tasks

from config import get_config
from data.notify_repo import NotifyRepo, YamlNotifyRepo
from lib.notify.config import CODE_MUTED, CODE_UNKNOWN, CODE_UNMUTED

class NotifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = get_config()
        self.repo: NotifyRepo = YamlNotifyRepo() # might replace with SQL-based repo later

        self.status = defaultdict(lambda: CODE_UNKNOWN) # technically the same as defaultdict(int). But that's only because UNKNOWN = 0, arbitrary.

    def cog_unload(self):
        self.check_mutestatus.cancel()

    async def broadcast_mute_status_update(self, user: discord.User, channel: discord.VoiceChannel, muted: bool):
        # Rule processing
        for rule in self.config.notify.mutenotify_rules:
            # print(f"Processing rule {rule.name} with user {rule.id}. Event user = {user.id}")
            if rule.id != user.id:
                continue
            rule.set_status(CODE_MUTED if muted else CODE_UNMUTED)

    @commands.command()
    async def mutenotify(self, ctx: commands.Context, user: discord.User, value: bool):
        if (not self.config.is_staff(ctx.author)):
            await ctx.reply("You must be staff to use this command :(")
            return
        
        # check that this does anything
        current_setting = user.id in (await self.repo.get_mutenotify_users())
        if value == current_setting:
            await ctx.reply(f"Mutenotify for {user.display_name} is already {value}")
            return

        if value:
            await self.repo.add_mutenotify_users([user.id])
        else:
            await self.repo.remove_mutenotify_users([user.id])
        await ctx.reply("Success!")

    @commands.Cog.listener()
    async def on_ready(self):
        #print("Starting mutestatus check")
        self.check_mutestatus.start()

    @tasks.loop(seconds=1.0)
    async def check_mutestatus(self):
        observed_users = set(await self.repo.get_mutenotify_users())
        #print("Running mute status update:")
        #print(f"\tObserved Users: {observed_users}")
        #print(f"\tStatus: {dict(self.status)}")
        to_update: list[tuple[discord.Member, discord.VoiceChannel, bool]] = []
        for guild_id in self.config.listening_guilds:
            guild = self.bot.get_guild(guild_id)
            channels = guild.channels
            for channel in channels:
                if channel.type != discord.ChannelType.voice:
                    continue
                for member in channel.members:
                    if member.id not in observed_users:
                        continue
                    muted = member.voice.mute or member.voice.self_mute or member.voice.suppress
                    curr_status = CODE_MUTED if muted else CODE_UNMUTED
                    if self.status[member.id] != curr_status:
                        to_update.append((member, channel, muted))
                        self.status[member.id] = curr_status
        
        if len(to_update) > 0:
            # execute all broadcasts asynchronously, not sequentially
            # print("Updating cases:")
            # for u,c,m in to_update:
            #     print(f"{u.display_name} mute status in {c.name} is not {m}")
            await asyncio.gather(*[self.broadcast_mute_status_update(*args) for args in to_update])

async def setup(bot: commands.Bot):
    await bot.add_cog(NotifyCog(bot))