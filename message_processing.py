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

import commands.randomgen_commands
import commands.cah_commands
import commands.dice_commands
import commands.misc_commands
import commands.battlegroup_commands

def run():
    """
    entry point; gets bot to run
    """
    logger.indicate_process_start("Connecting ..." + " " * 85)
    global client
    if client.is_closed():
        client = make_client()
    client.run(auth_data["token"])

@client.event
async def on_ready():
    time_display_template = data["config"]["time display template"]
    logger.indicate_process_outcome(f"Ready\n{datetime.datetime.now().strftime(time_display_template)}")
    logger.log_line("Initiate routines ...")
    logger.log_line("Ready")


@client.event
async def on_connect():
    logger.log("Connected")


@client.event
async def on_disconnect():
    time_display_template = data["config"]["time display template"]
    logger.log_line(f"Client disconnected at {datetime.datetime.now().strftime(time_display_template)}\n###\n")
