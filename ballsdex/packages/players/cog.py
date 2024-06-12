import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from tortoise.expressions import Q

from ballsdex.core.models import BallInstance, DonationPolicy
from ballsdex.core.models import Player as PlayerModel
from ballsdex.core.models import PrivacyPolicy, Trade, TradeObject
from ballsdex.core.utils.buttons import ConfirmChoiceView
from ballsdex.settings import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class Player(commands.GroupCog):
    """
    Manage your account settings.
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot
        if not self.bot.intents.members:
            self.__cog_app_commands_group__.get_command("privacy").parameters[  # type: ignore
                0
            ]._Parameter__parent.choices.pop()  # type: ignore

    @app_commands.command()
    @app_commands.choices(
        policy=[
            app_commands.Choice(name="Open Inventory", value=PrivacyPolicy.ALLOW),
            app_commands.Choice(name="Private Inventory", value=PrivacyPolicy.DENY),
            app_commands.Choice(name="Same Server", value=PrivacyPolicy.SAME_SERVER),
        ]
    )
    async def privacy(self, interaction: discord.Interaction, policy: PrivacyPolicy):
        """
        Set your privacy policy.
        """
        if policy == PrivacyPolicy.SAME_SERVER and not self.bot.intents.members:
            await interaction.response.send_message(
                "I need the `members` intent to use this policy.", ephemeral=True
            )
            return
        player, _ = await PlayerModel.get_or_create(discord_id=interaction.user.id)
        player.privacy_policy = policy
        await player.save()
        await interaction.response.send_message(
            f"Your privacy policy has been set to **{policy.name}**.", ephemeral=True
        )

<<<<<<< HEAD
        entries: list[tuple[str, str]] = []

        def fill_fields(title: str, emoji_ids: set[int]):
            # check if we need to add "(continued)" to the field name
            first_field_added = False
            buffer = ""

            for emoji_id in emoji_ids:
                emoji = self.bot.get_emoji(emoji_id)
                if not emoji:
                    continue

                text = f"{emoji} "
                if len(buffer) + len(text) > 1024:
                    # hitting embed limits, adding an intermediate field
                    if first_field_added:
                        entries.append(("\u200B", buffer))
                    else:
                        entries.append((f"__**{title}**__", buffer))
                        first_field_added = True
                    buffer = ""
                buffer += text

            if buffer:  # add what's remaining
                if first_field_added:
                    entries.append(("\u200B", buffer))
                else:
                    entries.append((f"__**{title}**__", buffer))

        if owned_countryballs:
            # Getting the list of emoji IDs from the IDs of the owned countryballs
            fill_fields(
                f"Owned {settings.collectible_name}s",
                set(bot_countryballs[x] for x in owned_countryballs),
            )
        else:
            entries.append((f"__**Owned {settings.collectible_name}s**__", "Nothing yet."))

        if missing := set(y for x, y in bot_countryballs.items() if x not in owned_countryballs):
            fill_fields(f"Missing {settings.collectible_name}s", missing)
        else:
            entries.append(
                (
                    f"__**:tada: No missing {settings.collectible_name}, "
                    "congratulations! :tada:**__",
                    "\u200B",
                )
            )  # force empty field value

        source = FieldPageSource(entries, per_page=5, inline=False, clear_description=False)
        source.embed.description = (
            f"{settings.bot_name} progression: "
            f"**{round(len(owned_countryballs)/len(bot_countryballs)*100, 1)}%**"
        )
        source.embed.colour = discord.Colour.blurple()
        source.embed.set_author(name=user_obj.display_name, icon_url=user_obj.display_avatar.url)

        pages = Pages(source=source, interaction=interaction, compact=True)
        await pages.start()

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def info(self, interaction: discord.Interaction, countryball: BallInstanceTransform):
        """
        Display info from a specific countryball.

        Parameters
        ----------
        countryball: BallInstance
            The countryball you want to inspect
        """
        if not countryball:
            return
        await interaction.response.defer(thinking=True)
        content, file = await countryball.prepare_for_message(interaction)
        await interaction.followup.send(content=content, file=file)
        file.close()

    @app_commands.command()
    async def rarity(self, interaction: discord.Interaction):
         # DO NOT CHANGE THE CREDITS TO THE AUTHOR HERE!
        """
        Show the rarity list of the dex. - made by GamingadlerHD
        """
        # Filter enabled collectibles
        enabled_collectibles = [x for x in balls.values() if x.enabled]

        if not enabled_collectibles:
            await interaction.response.send_message(
                f"There are no fictionalballs registered on this bot yet.",
                ephemeral=True,
            )
            return

        # Sort collectibles by rarity in ascending order
        sorted_collectibles = sorted(enabled_collectibles, key=lambda x: x.rarity)

        entries = []

        for collectible in sorted_collectibles:
            name = f"{collectible.country}"
            emoji = self.bot.get_emoji(collectible.emoji_id)

            if emoji:
                emote = str(emoji)
            else:
                emote = "N/A"
            #if you want the Rarity to only show full numbers like 1 or 12 use the code part here:
            # rarity = int(collectible.rarity)
            # otherwise you want to display numbers like 1.5, 5.3, 76.9 use the normal part.
            rarity = collectible.rarity

            entry = (name, f"{emote} Top: {rarity}")
            entries.append(entry)
        # This is the number of countryballs who are displayed at one page, 
        # you can change this, but keep in mind: discord has an embed size limit.
        per_page = 5 

        source = FieldPageSource(entries, per_page=per_page, inline=False, clear_description=False)
        source.embed.description = (
            f"__**{settings.bot_name} rarity**__"
        )
        source.embed.colour = discord.Colour.blurple()
        source.embed.set_author(
            name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
        )

        pages = Pages(source=source, interaction=interaction, compact=True)
        await pages.start()

    @app_commands.command()
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def last(self, interaction: discord.Interaction, user: discord.Member | None = None):
        """
        Display info of your or another users last caught countryball.

        Parameters
        ----------
        user: discord.Member
            The user you would like to see
        """
        user_obj = user if user else interaction.user
        await interaction.response.defer(thinking=True)
        try:
            player = await Player.get(discord_id=user_obj.id)
        except DoesNotExist:
            msg = f"{'You do' if user is None else f'{user_obj.display_name} does'}"
            await interaction.followup.send(
                f"{msg} not have any {settings.collectible_name} yet.",
                ephemeral=True,
            )
            return

        countryball = await player.balls.all().order_by("-id").first().select_related("ball")
        if not countryball:
            msg = f"{'You do' if user is None else f'{user_obj.display_name} does'}"
            await interaction.followup.send(
                f"{msg} not have any {settings.collectible_name} yet.",
                ephemeral=True,
            )
            return

        content, file = await countryball.prepare_for_message(interaction)
        await interaction.followup.send(content=content, file=file)
        file.close()

    @app_commands.command()
    async def favorite(self, interaction: discord.Interaction, countryball: BallInstanceTransform):
        """
        Set favorite countryballs.

        Parameters
        ----------
        countryball: BallInstance
            The countryball you want to set/unset as favorite
        """
        if not countryball:
            return

        if not countryball.favorite:
            player = await Player.get(discord_id=interaction.user.id).prefetch_related("balls")
            if await player.balls.filter(favorite=True).count() > 20:
                await interaction.response.send_message(
                    f"You cannot set more than 20 favorite {settings.collectible_name}s.",
                    ephemeral=True,
                )
                return

            countryball.favorite = True  # type: ignore
            await countryball.save()
            emoji = self.bot.get_emoji(countryball.countryball.emoji_id) or ""
            await interaction.response.send_message(
                f"{emoji} `#{countryball.pk:0X}` {countryball.countryball.country} "
                f"is now a favorite {settings.collectible_name}!",
                ephemeral=True,
            )

        else:
            countryball.favorite = False  # type: ignore
            await countryball.save()
            emoji = self.bot.get_emoji(countryball.countryball.emoji_id) or ""
            await interaction.response.send_message(
                f"{emoji} `#{countryball.pk:0X}` {countryball.countryball.country} "
                f"isn't a favorite {settings.collectible_name} anymore.",
                ephemeral=True,
            )

=======
>>>>>>> upstream/master
    @app_commands.command()
    @app_commands.choices(
        policy=[
            app_commands.Choice(name="Accept all donations", value=DonationPolicy.ALWAYS_ACCEPT),
            app_commands.Choice(
                name="Request your approval first", value=DonationPolicy.REQUEST_APPROVAL
            ),
            app_commands.Choice(name="Deny all donations", value=DonationPolicy.ALWAYS_DENY),
        ]
    )
    async def donation_policy(
        self, interaction: discord.Interaction, policy: app_commands.Choice[int]
    ):
        """
        Change how you want to receive donations from /balls give

        Parameters
        ----------
        policy: DonationPolicy
            The new policy for accepting donations
        """
        player, _ = await PlayerModel.get_or_create(discord_id=interaction.user.id)
        player.donation_policy = DonationPolicy(policy.value)
        if policy.value == DonationPolicy.ALWAYS_ACCEPT:
            await interaction.response.send_message(
                f"Setting updated, you will now receive all donated {settings.collectible_name}s "
                "immediately."
            )
        elif policy.value == DonationPolicy.REQUEST_APPROVAL:
            await interaction.response.send_message(
                "Setting updated, you will now have to approve donation requests manually."
            )
        elif policy.value == DonationPolicy.ALWAYS_DENY:
            await interaction.response.send_message(
                "Setting updated, it is now impossible to use "
                f"`/{settings.players_group_cog_name} give` with "
                "you. It is still possible to perform donations using the trade system."
            )
        else:
            await interaction.response.send_message("Invalid input!")
            return
        await player.save()  # do not save if the input is invalid

    @app_commands.command()
    async def delete(self, interaction: discord.Interaction):
        """
        Delete your player data.
        """
        view = ConfirmChoiceView(interaction)
        await interaction.response.send_message(
            "Are you sure you want to delete your player data?", view=view, ephemeral=True
        )
        await view.wait()
        if view.value is None or not view.value:
            return
        player, _ = await PlayerModel.get_or_create(discord_id=interaction.user.id)
        await player.delete()

    @app_commands.command()
    @app_commands.choices(
        type=[
            app_commands.Choice(name=settings.collectible_name.title(), value="balls"),
            app_commands.Choice(name="Trades", value="trades"),
            app_commands.Choice(name="All", value="all"),
        ]
    )
    async def export(self, interaction: discord.Interaction, type: str):
        """
        Export your player data.
        """
        player = await PlayerModel.get_or_none(discord_id=interaction.user.id)
        if player is None:
            await interaction.response.send_message(
                "You don't have any player data to export.", ephemeral=True
            )
            return
        await interaction.response.defer()
        files = []
        if type == "balls":
            data = await get_items_csv(player)
            filename = f"{interaction.user.id}_{settings.collectible_name}.csv"
            data.filename = filename  # type: ignore
            files.append(data)
        elif type == "trades":
            data = await get_trades_csv(player)
            filename = f"{interaction.user.id}_trades.csv"
            data.filename = filename  # type: ignore
            files.append(data)
        elif type == "all":
            balls = await get_items_csv(player)
            trades = await get_trades_csv(player)
            balls_filename = f"{interaction.user.id}_{settings.collectible_name}.csv"
            trades_filename = f"{interaction.user.id}_trades.csv"
            balls.filename = balls_filename  # type: ignore
            trades.filename = trades_filename  # type: ignore
            files.append(balls)
            files.append(trades)
        else:
            await interaction.followup.send("Invalid input!", ephemeral=True)
            return
        zip_file = BytesIO()
        with zipfile.ZipFile(zip_file, "w") as z:
            for file in files:
                z.writestr(file.filename, file.getvalue())
        zip_file.seek(0)
        if zip_file.tell() > 25_000_000:
            await interaction.followup.send(
                "Your data is too large to export."
                "Please contact the bot support for more information.",
                ephemeral=True,
            )
            return
        files = [discord.File(zip_file, "player_data.zip")]
        try:
            await interaction.user.send("Here is your player data:", files=files)
            await interaction.followup.send(
                "Your player data has been sent via DMs.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send the player data to you in DM. "
                "Either you blocked me or you disabled DMs in this server.",
                ephemeral=True,
            )


async def get_items_csv(player: PlayerModel) -> BytesIO:
    """
    Get a CSV file with all items of the player.
    """
    balls = await BallInstance.filter(player=player).prefetch_related(
        "ball", "trade_player", "special"
    )
    txt = (
        f"id,hex id,{settings.collectible_name},catch date,trade_player"
        ",special,shiny,attack,attack bonus,hp,hp_bonus\n"
    )
    for ball in balls:
        txt += (
            f"{ball.id},{ball.id:0X},{ball.ball.country},{ball.catch_date},"  # type: ignore
            f"{ball.trade_player.discord_id if ball.trade_player else 'None'},{ball.special},"
            f"{ball.shiny},{ball.attack},{ball.attack_bonus},{ball.health},{ball.health_bonus}\n"
        )
    return BytesIO(txt.encode("utf-8"))


async def get_trades_csv(player: PlayerModel) -> BytesIO:
    """
    Get a CSV file with all trades of the player.
    """
    trade_history = (
        await Trade.filter(Q(player1=player) | Q(player2=player))
        .order_by("date")
        .prefetch_related("player1", "player2")
    )
    txt = "id,date,player1,player2,player1 received,player2 received\n"
    for trade in trade_history:
        player1_items = await TradeObject.filter(
            trade=trade, player=trade.player1
        ).prefetch_related("ballinstance")
        player2_items = await TradeObject.filter(
            trade=trade, player=trade.player2
        ).prefetch_related("ballinstance")
        txt += (
            f"{trade.id},{trade.date},{trade.player1.discord_id},{trade.player2.discord_id},"
            f"{','.join([i.ballinstance.to_string() for i in player2_items])},"  # type: ignore
            f"{','.join([i.ballinstance.to_string() for i in player1_items])}\n"  # type: ignore
        )
    return BytesIO(txt.encode("utf-8"))
