from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, cast

import discord
from discord.ui import Button, Modal, TextInput, View
from prometheus_client import Counter
from tortoise.timezone import now as datetime_now

from ballsdex.core.models import BallInstance, Player, specials
from ballsdex.settings import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot
    from ballsdex.core.models import Special
    from ballsdex.packages.countryballs.countryball import CountryBall

log = logging.getLogger("ballsdex.packages.countryballs.components")
caught_balls = Counter(
    "caught_cb", "Caught countryballs", ["country", "shiny", "special", "guild_size"]
)


class CountryballNamePrompt(Modal, title=f"Atrapa a este {settings.collectible_name}."):
    name = TextInput(
        label="Name of this fictional country", style=discord.TextStyle.short, placeholder="Your guess"
    )

    def __init__(self, ball: "CountryBall", button: CatchButton):
        super().__init__()
        self.ball = ball
        self.button = button

    async def on_error(self, interaction: discord.Interaction, error: Exception, /) -> None:
        log.exception("An error ocurred in fictionalball catching prompt.", exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send("An error occured with this fictionalball.")
        else:
            await interaction.response.send_message("An error occured with this fictionalball.")

    async def on_submit(self, interaction: discord.Interaction["BallsDexBot"]):
        # TODO: use lock
        if self.ball.catched:
            await interaction.response.send_message(
                f"{interaction.user.mention} This fictionalball was caught!"
            )
            return
        if self.ball.model.catch_names:
            possible_names = (self.ball.name.lower(), *self.ball.model.catch_names.split(";"))
        else:
            possible_names = (self.ball.name.lower(),)
        if self.name.value.lower().strip() in possible_names:
            self.ball.catched = True
            await interaction.response.defer(thinking=True)
            ball, has_caught_before = await self.catch_ball(
                interaction.client, cast(discord.Member, interaction.user)
            )

            special = ""
            if ball.shiny:
                special += f"✨ ***Congratulations! You got a shiny fictionalball!*** ✨\n"
            if ball.specialcard and ball.specialcard.catch_phrase:
                special += f"*{ball.specialcard.catch_phrase}*\n"
            if has_caught_before:
                special += (
                    f"This fictionalball is a **new fictionalball** "
                    "in your completion."
                )

            await interaction.followup.send(
                f"{interaction.user.mention} You caught **{self.ball.name}!** "
                f"(`#{ball.pk:0X}`)\n\n{special}",
            )
            self.button.disabled = True
            await interaction.followup.edit_message(self.ball.message.id, view=self.button.view)
        else:
            await interaction.response.send_message(f"{interaction.user.mention} Wrong Name. Your answer: {self.name.value.lower().strip()}.")

    async def catch_ball(
        self, bot: "BallsDexBot", user: discord.Member
    ) -> tuple[BallInstance, bool]:
        player, created = await Player.get_or_create(discord_id=user.id)

        # stat may vary by +/- 20% of base stat
        bonus_attack = random.randint(-20, 20)
        bonus_health = random.randint(-20, 20)
        shiny = random.randint(1, 1000) == 1

        # check if we can spawn cards with a special background
        special: "Special | None" = None
        population = [x for x in specials.values() if x.start_date <= datetime_now() <= x.end_date]
        if not shiny and population:
            # Here we try to determine what should be the chance of having a common card
            # since the rarity field is a value between 0 and 1, 1 being no common
            # and 0 only common, we get the remaining value by doing (1-rarity)
            # We the sum each value for each current event, and we should get an algorithm
            # that kinda makes sense.
            common_weight = sum(1 - x.rarity for x in population)

            weights = [x.rarity for x in population] + [common_weight]
            # None is added representing the common countryball
            special = random.choices(population=population + [None], weights=weights, k=1)[0]

        is_new = not await BallInstance.filter(player=player, ball=self.ball.model).exists()
        ball = await BallInstance.create(
            ball=self.ball.model,
            player=player,
            shiny=shiny,
            special=special,
            attack_bonus=bonus_attack,
            health_bonus=bonus_health,
            server_id=user.guild.id,
        )
        if user.id in bot.catch_log:
            log.info(
                f"{user} caught {settings.collectible_name}"
                f" {self.ball.model}, {shiny=} {special=}",
            )
        else:
            log.debug(
                f"{user} caught {settings.collectible_name}"
                f" {self.ball.model}, {shiny=} {special=}",
            )
        if user.guild.member_count:
            caught_balls.labels(
                country=self.ball.model.country,
                shiny=shiny,
                special=special,
                # observe the size of the server, rounded to the nearest power of 10
                guild_size=10 ** math.ceil(math.log(max(user.guild.member_count - 1, 1), 10)),
            ).inc()
        return ball, is_new


class CatchButton(Button):
    def __init__(self, ball: "CountryBall"):
        super().__init__(style=discord.ButtonStyle.primary, label="¡Atrápame!")
        self.ball = ball

    async def callback(self, interaction: discord.Interaction):
        if self.ball.catched:
            await interaction.response.send_message(f"Ya atraparon a esta {settings.collectible_name}.", ephemeral=True)
        else:
            await interaction.response.send_modal(CountryballNamePrompt(self.ball, self))


class CatchView(View):
    def __init__(self, ball: "CountryBall"):
        super().__init__()
        self.ball = ball
        self.button = CatchButton(ball)
        self.add_item(self.button)

    async def interaction_check(self, interaction: discord.Interaction["BallsDexBot"], /) -> bool:
        return await interaction.client.blacklist_check(interaction)

    async def on_timeout(self):
        self.button.disabled = True
        if self.ball.message:
            try:
                await self.ball.message.edit(view=self)
            except discord.HTTPException:
                pass
