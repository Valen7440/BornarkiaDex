import discord
import logging
import random

from discord import app_commands
from discord.ui import Button
from discord.ext import commands
from discord.utils import format_dt
from tortoise.exceptions import IntegrityError, DoesNotExist
from collections import defaultdict
from typing import TYPE_CHECKING, cast
from ballsdex.core.utils.buttons import ConfirmChoiceView

from ballsdex.settings import settings
from ballsdex.core.models import (
    GuildConfig,
)
from ballsdex.core.utils.transformers import BallTransform, SpecialTransform
from ballsdex.core.utils.paginator import FieldPageSource, TextPageSource, Pages
from ballsdex.core.utils.logging import log_action
from ballsdex.packages.countryballs.countryball import CountryBall

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot
    from ballsdex.packages.countryballs.cog import CountryBallsSpawner

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("ballsdex.packages.booster.cog")

@app_commands.guilds(*settings.booster_guilds_ids)
@app_commands.default_permissions(manage_roles=True)
class Booster(commands.GroupCog):
    """
    Bot booster commands.
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot
    
    @app_commands.command()
    @app_commands.checks.has_any_role(*settings.booster_role_ids)
    async def spawn(
        self,
        interaction: discord.Interaction,
        ball: BallTransform | None = None,
        channel: discord.TextChannel | None = None,
    ):
        """
        Forza el spawn de countryballs.

        Parameters
        ----------
        ball: ball | None
            Ball que quieres spawnear (si no elegis, se generara una aleatoria).
        channel: discord.TextChannel | None
            Canal en donde vas a spawnear la ball (si no se elige, se spawneara en el canal que has usado el comando).
        """
        # the transformer triggered a response, meaning user tried an incorrect input
        if interaction.response.is_done():
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not ball:
            countryball = await CountryBall.get_random()
        else:
            countryball = CountryBall(ball)
        await countryball.spawn(channel or interaction.channel)  # type: ignore
        await interaction.followup.send(
            f"{settings.collectible_name.title()} spawneada.", ephemeral=True
        )
        await log_action(
            f"{interaction.user} spawneada {settings.collectible_name} {countryball.name} "
            f"in {channel or interaction.channel}.",
            self.bot,
        )


    @app_commands.command()
    @app_commands.checks.has_any_role(*settings.booster_role_ids)
    async def guilds(
        self,
        interaction: discord.Interaction,
        user: discord.User | None = None,
        user_id: str | None = None,
    ):
        """
        Mira los servidores de un usuario. Pon la ID de un usuario en `user_id` o selecciona a un usuario en `user`.

        Parameters
        ----------
        user: discord.User | None
            Mira los servidores de un usuario, si es que está en el servidor.
        user_id: str | None
            Pon la ID de un usuario para ver en que servidores tiene a BornarkiaDex, si es que no está en el servidor.
        """
        if (user and user_id) or (not user and not user_id):
            await interaction.response.send_message(
                "Tienes que poner a un usuario en `user` o una ID de un usuario en `user_id`.", ephemeral=True
            )
            return

        if not user:
            try:
                user = await self.bot.fetch_user(int(user_id))  # type: ignore
            except ValueError:
                await interaction.response.send_message(
                    "La ID de ese usuario, no es válida.", ephemeral=True
                )
                return
            except discord.NotFound:
                await interaction.response.send_message(
                    "La ID de ese usuario, no existe.", ephemeral=True
                )
                return

        if self.bot.intents.members:
            guilds = user.mutual_guilds
        else:
            guilds = [x for x in self.bot.guilds if x.owner_id == user.id]

        if not guilds:
            if self.bot.intents.members:
                await interaction.response.send_message(
                    f"El usuario no tiene ningun servidor con {settings.bot_name}.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"El usuario no tiene ningun servidor con {settings.bot_name}.\n"
                    ":warning: *El bot no detecta los servidores con los que esta el usuario, sino "
                    "solo los servidores en donde esta el bot y son propietarios de ese servidor.*",
                    ephemeral=True,
                )
            return

        entries: list[tuple[str, str]] = []
        for guild in guilds:
            if config := await GuildConfig.get_or_none(guild_id=guild.id):
                spawn_enabled = config.enabled and config.guild_id
            else:
                spawn_enabled = False

            field_name = f"`{guild.id}`"
            field_value = ""

            # highlight suspicious server names
            if any(x in guild.name.lower() for x in ("farm", "grind", "spam")):
                field_value += f"- :warning: **{guild.name}**\n"
            else:
                field_value += f"- {guild.name}\n"

            # highlight low member count
            if guild.member_count <= 3:  # type: ignore
                field_value += f"- :warning: **{guild.member_count} miembros**\n"
            else:
                field_value += f"- {guild.member_count} miembros\n"

            # highlight if spawning is enabled
            if spawn_enabled:
                field_value += "- :warning: **El Spawn esta activado.**"
            else:
                field_value += "- El Spawn esta desactivado."

            entries.append((field_name, field_value))

        source = FieldPageSource(entries, per_page=25, inline=True)
        source.embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)

        if len(guilds) > 1:
            source.embed.title = f"{len(guilds)} servidores"
        else:
            source.embed.title = "1 servidor"

        if not self.bot.intents.members:
            source.embed.set_footer(
                text="\N{WARNING SIGN} El bot no detecta los servidores con los que esta el usuario, sino  "
                "solo los servidores en donde esta el bot y son propietarios de ese servidor."
            )

        pages = Pages(source=source, interaction=interaction, compact=True)
        pages.add_item(
            Button(
                style=discord.ButtonStyle.link,
                label="Mirar perfil",
                url=f"discord://-/users/{user.id}",
                emoji="\N{LEFT-POINTING MAGNIFYING GLASS}",
            )
        )
        await pages.start(ephemeral=True)
    