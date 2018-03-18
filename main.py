import logging
import datetime
import subsystems
from discord.ext import commands
import bot

## LOGGER
logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)

handler = logging.FileHandler(filename="logs/{}.log".format(datetime.date.today()), encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))

logger.addHandler(handler)

## GLOBALS
config = None
api = None
scheduler = None

INIT_EXT = {"cogs.owner", "cogs.channel", "cogs.discord", "cogs.monitor", "cogs.players", "cogs.server", "cogs.silly", "cogs.users"}

## CONFIG INIT
try:
    config = subsystems.Config("config.yml", logger)
    config.setup()
except subsystems.ConfigError as err:
    print("Error initializing Config object.")
    print(str(err))
    logger.error(err)
    raise RuntimeError("Stopping now.")

## API INIT
try:
    api = subsystems.API(config)
except subsystems.ApiError as err:
    print("Error initializing API object.")
    print(str(err))
    logger.error(err)
    raise RuntimeError("Stopping now.")

## BOT INIT
bot = bot.Borealis(config.bot["prefix"], config, api,
                   description="Borealis version 3, here to assist in any SS13 related matters!",
                   pm_help=True)

try:
    scheduler = subsystems.TaskScheduler(bot, config.scheduler["interval"], logger)
    scheduler.add_task(43200, config.update_users, "update_users", init_now=True,
                       args=[api], is_coro=True)
    scheduler.add_task(43200, config.update_channels, "update_channels", init_now=True,
                       args=[api], is_coro=True)
    scheduler.add_task(1800, bot.process_temporary_bans, "process_bans", init_now=True, is_coro=True)
except subsystems.SchedulerError as err:
    print("Error initializing scheduler object.")
    print(str(err))
    logger.error(err)
    raise RuntimeError("Stopping now.")

@bot.event
async def on_ready():
    logger.info("MAIN: Bot ready. Logged in as: %s - %s", bot.user.name, bot.user.id)
    print("Bot ready. Logged in as: {} - {}".format(bot.user.name, bot.user.id))

    if __name__ == '__main__':
        for ext in INIT_EXT:
            try:
                bot.load_extension(ext)
            except Exception:
                print("Failed to load extension: {}.".format(ext))
                logger.error("MAIN: Failed to load extension: %s.", ext)

    print("Start up successful.")
    logger.info("MAIN: Bot up and running.")

    bot.loop.create_task(scheduler.run_loop())

bot.run(config.bot["token"], bot=True, reconnect=True)
