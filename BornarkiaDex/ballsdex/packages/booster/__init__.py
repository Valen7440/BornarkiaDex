from typing import TYPE_CHECKING

from ballsdex.packages.booster.cog import Booster

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

async def setup(bot: "BallsDexBot"):
    await bot.add_cog(Booster(bot))