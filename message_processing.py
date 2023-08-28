import datetime
import importlib
from typing import Any

from data_backend import *

auth_data: dict[str, Any]
data: dict
logger: Logger
client = make_client()


data = load_all()
auth_data = load("auth")
logger = Logger()


def run():
    """
    entry point; gets bot to run
    """
    import commands.randomgen_commands
    import commands.cah_commands
    import commands.dice_commands
    import commands.misc_commands
    import commands.battlegroup_commands
    logger.indicate_process_start("Connecting ..." + " " * 85)
    global client
    if client.is_closed():
        client = make_client()
    client.run(auth_data["token"])

@client.event
async def on_ready():
    time_display_template = data["config"]["time display template"]
    logger.log_line(f"Ready\n{datetime.datetime.now().strftime(time_display_template)}")

@client.event
async def on_connect():
    logger.log_line("Connected")


@client.event
async def on_disconnect():
    time_display_template = data["config"]["time display template"]
    logger.log_line(f"Client disconnected at {datetime.datetime.now().strftime(time_display_template)}\n###\n")
