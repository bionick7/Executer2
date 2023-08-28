import json
import sys
import os
import traceback
import discord
from discord.ext import commands
from typing import Any, Union

from shutil import get_terminal_size


class Logger:
    def __init__(self, p_output_file=sys.stdout, p_error_file=sys.stderr, p_base_intend: int = 100):
        self._output_file = p_output_file
        self._error_file = p_error_file
        self.base_intend = p_base_intend

    def _get_terminal_size(self):
        outp, error = (150, 50), (150, 50)
        if self._output_file is sys.stdout:
            outp = get_terminal_size(fallback=(150, 50))
        if self._error_file is sys.stderr:
            error = get_terminal_size(fallback=(150, 50))
        return outp, error

    def log(self, text: str, is_error=False):
        if is_error:
            self._error_file.write(text)
        else:
            self._output_file.write(text)

    def indicate_process_start(self, text: str):
        outp_size, _ = self._get_terminal_size()
        intend = min(self.base_intend, outp_size[0] - 20)
        space = max(intend - len(text), 0)
        self.log(text + " " * space)
        self._output_file.flush()

    def log_line(self, text: str):
        self.log(text + "\n")

    def log_block(self, *args):
        for a in args:
            self.log(a.__str__() + "\n")

    def log_objects(self, **kwargs):
        for name, value in kwargs.items():
            self.log(f"{name}: {value.__str__()}\n")

    def log_traceback(self):
        traceback.print_exc(file=self._error_file)

    def __repr__(self):
        out, err = self._get_terminal_size()
        return f"<Logger object @ ({out[0]}; {out[1]})| Error ({err[0]}; {err[1]})>"


def make_client() -> commands.Bot:
    intents = discord.Intents.default()
    intents.reactions = True
    intents.members = True
    intents.message_content = True
    intents.dm_messages = True
    intents.guild_messages = True
    intents.dm_reactions = True
    intents.guild_reactions = True
    return commands.Bot(command_prefix="%", intents=intents)


def correct_dict(dict_: dict) -> dict:
    for k, field in dict_.items():
        if isinstance(field, dict):
            dict_[k] = correct_dict(field)
        elif isinstance(field, list):
            dict_[k] = list(correct_dict(dict(zip(range(len(field)), field))).values())
        elif isinstance(field, str):
            if field.startswith("x"):
                dict_[k] = int(field[1:], base=16)
    return dict_


def load(name, logger=None, encoding="utf-8") -> dict[str, Any]:
    """
    loads a json module and returns the result s a dictionary
    """
    path = f"configs/{name}.json"
    if logger is not None:
        logger.indicate_process_start("Loading: " + path + "...")
    try:
        with open(path, encoding=encoding) as f:
            data: dict = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {
            "__meta__": {
                "errors": [e],
                "outcome": "fatal error",
                "filepath": path,
                "filename": path.split("/")[-1]
            }
          }

    if logger is not None:
        logger.indicate_process_outcome("Success")
    data = correct_dict(data)

    data["__meta__"] = {
        "errors": [],
        "outcome": "success",
        "filepath": path,
        "filename": path.split("/")[-1]
    }
    return data


def can_load(name):
    """
    checks if a json module of this name is available
    """
    directory = os.path.dirname(__file__)
    #print(os.path.join(directory, "configs", name + ".json"))
    return os.path.isfile(os.path.join(directory, "configs", name + ".json"))


def save(name, data):
    """
    saves a dictionary as a json module by a given name
    """
    with open("configs/{0}.json".format(name), encoding="UTF-8") as f:
        json.dump(data, f)


def load_all(logger=None):
    """
    loads all modules specified in the entrance file
    """
    res = {}
    if can_load("config"):
        res["config"] = load("config", logger)
    if can_load("cah_config"):
        res["cah_config"] = load("cah_config", logger)
    return res


async def get_dm_channel(user: Union[discord.User, discord.Member]) -> discord.DMChannel:
    channel = user.dm_channel
    if channel is None:
        channel = await user.create_dm()
    return channel


if __name__ == '__main__':
    print(can_load("s"))
