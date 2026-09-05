import logging
import logging.handlers
import os
import platform
from importlib.metadata import version

import discord
from discord import app_commands
from discord.ext.commands import has_permissions
from dotenv import load_dotenv


# make your own .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BERN_ID = os.getenv("BERN_ID")
BERN_GUILD = os.getenv("BERN_GUILD")

# this is just for my end, BERN_ID and BERN_GUILD are not really required, you can change that
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")
if not BERN_ID:
    raise RuntimeError("BERN_ID is not set.")
if not BERN_GUILD:
    raise RuntimeError("BERN_GUILD is not set.")

OWNER_ID = int(BERN_ID)
GUILD_ID = int(BERN_GUILD)


# logging part

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

logging.getLogger("discord.http").setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="logs/discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,
    backupCount=5,
)

dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}",
    dt_fmt,
    style="{",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


# client part

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID


# events part

@client.event
async def on_ready():
    await tree.sync()

    print("Ready to engage!")

    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"in {len(client.guilds)} servers!",
        )
    )


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user or message.author.bot:
        return

    if client.user and client.user.mentioned_in(message):
        await message.channel.send(
            "You can type `/commands` for more info!"
        )


# commands part

@tree.command(
    name="sync",
    description="Owner only",
    guild=discord.Object(id=GUILD_ID),
)
async def sync(interaction: discord.Interaction):
    if not is_owner(interaction):
        await interaction.response.send_message(
            "You must be the owner to use this command!",
            ephemeral=True,
        )
        return

    await tree.sync()
    await interaction.response.send_message(
        "Sync réussi",
        ephemeral=True,
    )
    print("Command tree synced.")


@tree.command(name="info", description="Get information about the bot")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello! I'm the Bern Bot! I currently run under "
        f"`Python {platform.python_version()}` with "
        f"`discord.py {version('discord.py')}`!",
        ephemeral=True,
    )


@tree.command(name="ping", description="Test bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong! In {round(client.latency * 1000)}ms."
    )


@tree.command(name="commands", description="Get list of commands")
async def commands(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**Commands**",
        url="https://github.com/Bukuo/Bernbot",
        description="List of commands",
    )
    embed.set_thumbnail(
        url=(
            "https://cdn.discordapp.com/avatars/"
            "1041023255089270816/"
            "41e68056f8c180e90af7c756dff3786?size=1024"
        )
    )

    embed.add_field(
        name="**Users commands**",
        value=" ",
        inline=False,
    )
    embed.add_field(
        name="/info",
        value="Get information about the bot",
        inline=False,
    )
    embed.add_field(
        name="/commands",
        value="Get list of commands",
        inline=False,
    )
    embed.add_field(
        name="/ping",
        value="Test bot's latency",
        inline=False,
    )
    embed.add_field(
        name="/avatar",
        value="Retrieve user's avatar (if he has one)",
        inline=False,
    )
    embed.add_field(
        name="/banner",
        value="Retrieve user's banner (if he has one)",
        inline=False,
    )
    embed.add_field(
        name="/wisetree",
        value="Summon 'that' tree",
        inline=False,
    )
    embed.add_field(
        name="/invite",
        value="Get invite link",
        inline=False,
    )

    embed.add_field(
        name="**Staff commands**",
        value=" ",
        inline=False,
    )
    embed.add_field(
        name="/mute",
        value="Mute specified user",
        inline=False,
    )
    embed.add_field(
        name="/unmute",
        value="Unmute specified user",
        inline=False,
    )
    embed.add_field(
        name="/ban",
        value="Ban specified user",
        inline=False,
    )
    embed.add_field(
        name="/clear",
        value="Purge an amount of messages",
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


@tree.command(name="clear", description="Purge amount of messages")
@has_permissions(manage_roles=True)
@discord.app_commands.checks.bot_has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message(
        f"Cleared {amount} message(s).",
        ephemeral=True,
    )
    await interaction.channel.purge(limit=amount)
    print(f"Purged {amount} message(s) by {interaction.user}")


@tree.command(name="mute", description="Mute specified user")
@has_permissions(manage_messages=True, manage_roles=True)
@discord.app_commands.checks.bot_has_permissions(
    manage_messages=True,
    manage_roles=True,
)
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str,
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    muted_role = discord.utils.get(guild.roles, name="Muted")

    if not muted_role:
        muted_role = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(
                muted_role,
                speak=False,
                send_messages=False,
            )

    if muted_role in member.roles:
        await interaction.response.send_message(
            "User is already muted!",
            ephemeral=True,
        )
        print(
            f"{interaction.user} tried to mute already muted user {member}!"
        )
        return

    await member.add_roles(muted_role, reason=reason)
    await interaction.response.send_message(
        f"Muted {member.mention} for reason: {reason}"
    )
    print(f"{interaction.user} muted {member}: {reason}")


@tree.command(name="unmute", description="Unmute specified user")
@has_permissions(manage_messages=True, manage_roles=True)
@discord.app_commands.checks.bot_has_permissions(
    manage_messages=True,
    manage_roles=True,
)
async def unmute(
    interaction: discord.Interaction,
    member: discord.Member,
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    muted_role = discord.utils.get(guild.roles, name="Muted")

    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await interaction.response.send_message(
            f"Unmuted {member.mention}"
        )
        print(f"{interaction.user} unmuted {member}!")
        return

    await interaction.response.send_message(
        "User is not muted!",
        ephemeral=True,
    )
    print(f"{interaction.user} tried to unmute {member}!")


@tree.command(name="ban", description="ban the user")
@has_permissions(administrator=True, manage_messages=True, manage_roles=True)
@discord.app_commands.checks.bot_has_permissions(
    administrator=True,
    manage_messages=True,
    manage_roles=True,
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    *,
    reason: str,
):
    await member.ban(reason=reason)
    await interaction.response.send_message(
        f"{member} was banned for: {reason}"
    )
    print(f"{interaction.user} banned {member}: {reason}")


@tree.command(name="banner", description="Get user's banner (if he has one)")
async def banner(
    interaction: discord.Interaction,
    member: discord.Member,
):
    req = await client.http.request(
        discord.http.Route("GET", "/users/{uid}", uid=member.id)
    )
    banner_id = req["banner"]

    if banner_id:
        banner_url = (
            f"https://cdn.discordapp.com/banners/"
            f"{member.id}/{banner_id}?size=1024"
        )

        embed = discord.Embed(
            title=member.name,
            url=banner_url,
            description="User banner",
            colour=0x1F1E33,
        )
        embed.set_image(url=banner_url)
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.send_message(
        "User has no banner!",
        ephemeral=True,
    )


@tree.command(name="avatar", description="Get user's avatar (if he has one)")
async def avatar(
    interaction: discord.Interaction,
    member: discord.Member,
):
    req = await client.http.request(
        discord.http.Route("GET", "/users/{uid}", uid=member.id)
    )
    avatar_id = req["avatar"]

    if avatar_id:
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/"
            f"{member.id}/{avatar_id}?size=1024"
        )

        embed = discord.Embed(
            title=member.name,
            url=avatar_url,
            description="User avatar",
            colour=0x1F1E33,
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.send_message(
        "User has no avatar!",
        ephemeral=True,
    )


@tree.command(name="invite", description="Get invite link")
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message(
        "[Link](<https://bit.ly/BukuoBotLink>)",
        ephemeral=True,
    )


@tree.command(name="wisetree", description="Summon 'that' tree")
async def wise_tree(interaction: discord.Interaction):
    await interaction.response.send_message(
        "https://tenor.com/view/tree-wise-gif-26790708"
    )


# error handling part

@tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    if isinstance(error, app_commands.CheckFailure):
        message = "You don't have permission to use this command."
    else:
        message = "An error occurred while executing that command."
        print(f"Command error: {error}")

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)



if __name__ == "__main__":
    client.run(DISCORD_TOKEN, log_handler=handler)
