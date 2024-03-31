import os
import random
import discord
from discord import app_commands
from dotenv import load_dotenv
import logging
import logging.handlers
from importlib.metadata import version
import platform


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True
tree = app_commands.CommandTree(client)
guildid = 910934680268832808

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guildid))
    print("Ready to engage!")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"In {str(len(client.guilds))} servers!"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user.mentioned_in(message):
        await message.channel.send("You can type `/commands` for more info!")

@tree.command(name='sync', description='Owner only', guild=discord.Object(id=guildid))
async def sync(interaction: discord.Interaction):
    if interaction.user.id == 404296022941106177:
        await tree.sync()
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Sync réussi")
        print('Command tree synced.')
    else:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send('You must be the owner to use this command!')

@tree.command(name='reset', description='Owner only', guild=discord.Object(id=guildid))
async def sync(interaction: discord.Interaction):
    if interaction.user.id == 404296022941106177:
        await client
        print('Reseted.')
    else:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send('You must be the owner to use this command!')


@tree.command(name = "info", description = "Get information about the bot")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello! I'm the Bukuo Bot! I currently run under `Python {platform.python_version()}` with `discord.py {version('discord.py')}`!")

@tree.command(name = "ping", description = "Test bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! In {round(client.latency * 1000)}ms.')

@tree.command(name = "commands", description = "Get list of commands")
async def commands(interaction: discord.Interaction):
    embed=discord.Embed(title="**Commands**", url="https://github.com/Bukuo/Bukuobot", description="List of commands")
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1041023255089270816/41e68056f8c1809e90af7c756dff3786?size=1024")
    embed.add_field(name="/info", value="Get information about the bot", inline=False)
    embed.add_field(name="/commands", value="Get list of commands", inline=False)
    embed.add_field(name="/ping", value="Test bot's latency", inline=False)
    embed.add_field(name="/avatar", value="Retrieve user's avatar (if he has one)", inline=False)
    embed.add_field(name="/banner", value="Retrieve user's banner (if he has one)", inline=False)
    embed.add_field(name="/wisetree", value="Summon 'that' tree", inline=False)
    embed.add_field(name="/invite", value="Get invite link", inline=False)
    embed.add_field(name="**Admin commands**", value="From here are admin commands", inline=False)
    embed.add_field(name="/mute", value="Mute specified user", inline=False)
    embed.add_field(name="/unmute", value="Unmute specified user", inline=False)
    embed.add_field(name="/ban", value="Ban someone", inline=False)
    embed.add_field(name="/clear", value="Purge an amount of messages", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name = "clear", description = "Purge amount of messages")
@discord.app_commands.checks.bot_has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount:int):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"Cleared {amount} message(s).")
    await interaction.channel.purge(limit=amount)
    print(f"Purged {amount} message(s) by {interaction.user}")
    

@tree.command(name = "mute", description = "Mute specified user")
@discord.app_commands.checks.bot_has_permissions(manage_messages=True)
async def mute(interaction: discord.Interaction, member:discord.Member, reason:str):
    guild = interaction.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")

    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False)

    if mutedRole in member.roles:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("User is already muted!")
        print(f"{interaction.user} tried to mute already muted user {member}!")
    else:
        await member.add_roles(mutedRole, reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for reason: {reason}")
        print(f"{interaction.user} muted {member}: {reason}")
 
@tree.command(name = "unmute", description = "Unmute specified user")
@discord.app_commands.checks.bot_has_permissions(manage_messages=True)
async def unmute(interaction: discord.Interaction, member:discord.Member):
    guild = interaction.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")

    if mutedRole in member.roles:
        await member.remove_roles(mutedRole)
        await interaction.response.send_message(f"Unmuted {member.mention}")
        print(f"{interaction.user} unmuted {member}!")
    else:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("User is not muted!")
        print(f"{interaction.user} tried to unmute user {member}!")

@tree.command(name = "ban", description = "ban the user")
async def ban(interaction: discord.Interaction, member: discord.Member, *, reason:str):
    await member.ban(reason=reason)
    await interaction.response.send_message(f'{member} was banned for: {reason}')
    print(f"{interaction.user} banned {member}: {reason}")

@tree.command(name = "banner", description = "Retrieve user's banner (if he has one)")
async def banner(interaction: discord.Interaction, member:discord.Member):
    req = await client.http.request(discord.http.Route("GET","/users/{uid}",uid=member.id))
    banner_id = req["banner"]
    if banner_id:
        banner_url = f"https://cdn.discordapp.com/banners/{member.id}/{banner_id}?size=1024"

        embed = discord.Embed(title=f"{member.name}", url=banner_url, description="User banner", colour=0x1f1e33)
        embed.set_image(url=banner_url)
        await interaction.response.send_message(embed=embed)

@tree.command(name = "avatar", description = "Retrieve user's avatar (if he has one)")
async def avatar(interaction: discord.Interaction, member:discord.Member):
    req = await client.http.request(discord.http.Route("GET","/users/{uid}",uid=member.id))
    avatar_id = req["avatar"]
    if avatar_id:
        avatar_url = f"https://cdn.discordapp.com/avatars/{member.id}/{avatar_id}?size=1024"

        embed = discord.Embed(title=f"{member.name}", url=avatar_url, description="User avatar", colour=0x1f1e33)
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed)

@tree.command(name = "invite", description = "Get invite link")
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message("Link: https://bit.ly/BukuoBotLink")

@tree.command(name = "wisetree", description = "Summon 'that' tree")
async def wiseTree(interaction: discord.Interaction):
    await interaction.response.send_message("https://tenor.com/view/tree-wise-gif-26790708")


load_dotenv()
client.run(os.getenv("DISCORD_TOKEN"), log_handler=handler)