import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="k", intents=intents)

# 🔐 SETTINGS
LIMITS = {
    "channel_delete": 3,
    "role_delete": 3,
    "ban": 3
}

user_actions = {}
WHITELIST = [1234567890]  # put your Discord ID here

def track(user_id, action):
    if user_id not in user_actions:
        user_actions[user_id] = {
            "channel_delete": 0,
            "role_delete": 0,
            "ban": 0
        }

    user_actions[user_id][action] += 1

    # reset after 10 sec
    async def reset():
        await asyncio.sleep(10)
        user_actions[user_id][action] = 0

    bot.loop.create_task(reset())

    return user_actions[user_id][action]

# ✅ READY
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# 🔨 KICK COMMAND
@bot.command()
async def kick(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.kick_members:
        return await ctx.send("❌ No permission")

    await member.kick()
    await ctx.send(f"✅ {member} kicked")

# 🔨 BAN COMMAND
@bot.command()
async def ban(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.ban_members:
        return await ctx.send("❌ No permission")

    await member.ban()
    await ctx.send(f"🚫 {member} banned")

# 🧹 CLEAR COMMAND
@bot.command()
async def clear(ctx, amount: int):
    if not ctx.author.guild_permissions.manage_messages:
        return await ctx.send("❌ No permission")

    await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Deleted {amount} messages", delete_after=3)

# 🚨 CHANNEL DELETE DETECT
@bot.event
async def on_guild_channel_delete(channel):
    logs = await channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete).flatten()
    if not logs:
        return

    entry = logs[0]
    user = entry.user

    if user.id in WHITELIST or user.id == channel.guild.owner_id:
        return

    count = track(user.id, "channel_delete")

    if count >= LIMITS["channel_delete"]:
        member = channel.guild.get_member(user.id)
        await member.ban(reason="Anti-Nuke: Channel Delete")

# 🚨 ROLE DELETE DETECT
@bot.event
async def on_guild_role_delete(role):
    logs = await role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete).flatten()
    if not logs:
        return

    entry = logs[0]
    user = entry.user

    if user.id in WHITELIST or user.id == role.guild.owner_id:
        return

    count = track(user.id, "role_delete")

    if count >= LIMITS["role_delete"]:
        member = role.guild.get_member(user.id)
        await member.ban(reason="Anti-Nuke: Role Delete")

# 🚨 MASS BAN DETECT
@bot.event
async def on_member_ban(guild, user):
    logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).flatten()
    if not logs:
        return

    entry = logs[0]
    executor = entry.user

    if executor.id in WHITELIST or executor.id == guild.owner_id:
        return

    count = track(executor.id, "ban")

    if count >= LIMITS["ban"]:
        member = guild.get_member(executor.id)
        await member.ban(reason="Anti-Nuke: Mass Ban")

# 🔑 RUN BOT
bot.run("MTQ4NzEwOTIyMDUxOTM3OTIxNg.GrEK3t.T23630yuWsy9_BqWZ5aoyIksQgSIRv7FAzyI1c")