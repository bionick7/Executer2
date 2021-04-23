import discord

import backend
import data_backend

from pymongo import MongoClient
from pymongo.database import Database
from copy import deepcopy

__author__ = "ech#5002"

DEFAULT_FUNCTIONS = []

__data = data_backend.load_all()
__safe_data = deepcopy(__data)
del (__safe_data["auth"])
__client = discord.Client()
__output_queue = backend.Queue()
__database_client = None

DEFAULT_SERVER_DATA = {
    "discord_id": -1,
    "name": "NO SERVER",
    "functions": DEFAULT_FUNCTIONS,
    "cah_librairies": __data["cah config"]["full"],
    "youtube_follow_channels": {},
    "response_functions": {},
    "default_channel_id": -1
}

__response_dict = {}
__routine_list = {}

__globals_list = [__safe_data, __client, __database_client, __response_dict, __routine_list]

_global_dict = {
    **__data,
    "safe_data": __safe_data,
    "client": __client,
    "database_client": __database_client,
    "response_dict": __response_dict,
    "routine_list": __routine_list,
    "default server data": DEFAULT_SERVER_DATA,
    "logger": data_backend.logger,
    "database_access": True
}


def tr(token: str) -> str:
    return token


def reload():
    global __data, __safe_data, __client, __output_queue, __database_client, __response_dict, __routine_list, __globals_list, _global_dict

    __data = data_backend.load_all()
    __safe_data = deepcopy(__data)
    del (__safe_data["auth"])
    __client = discord.Client()
    __output_queue = backend.Queue()
    __database_client = None

    __response_dict = {}
    __routine_list = {}

    __globals_list = [__safe_data, __client, __database_client, __response_dict, __routine_list]

    _global_dict = {
        **__data,
        "safe_data": __safe_data,
        "client": __client,
        "database_client": __database_client,
        "response_dict": __response_dict,
        "routine_list": __routine_list,
        "default server data": DEFAULT_SERVER_DATA,
        "logger": data_backend.logger,
        "database_access": False
    }


def __set_dict(d, path, value):
    if len(path) > 1:
        __set_dict(d[path[0]], path[1:], value)
    else:
        d[path[0]] = value


def __get_dict(d, path, current_path=""):
    if isinstance(d, dict):
        if path[0] in d:
            if len(path) > 1:
                return __get_dict(d[path[0]], path[1:], current_path + path[0])
            else:
                return d[path[0]]
        else:
            raise KeyError(f"No such value '{path[0]}' in the dictionary '{current_path}'")
    elif isinstance(d, list):
        try:
            if len(path) > 1:
                return __get_dict(d[int(path[0])], path[1:], current_path + path[0])
            else:
                return d[path[0]]
        except ValueError as e:
            raise KeyError(f"Cannot index a list with a non int key: '{path[0]}'@'{current_path}'")
    elif isinstance(d, (MongoClient, Database)):
        try:
            if len(path) > 1:
                return __get_dict(d[path[0]], path[1:], current_path + path[0])
            else:
                return d[path[0]]
        except:
            raise KeyError(f"Client can't find the database: '{path[0]}'@'{current_path}'")
    else:
        raise ValueError(f"Cannot further subdivide {type(d)}: '{path[0]}'@'{current_path}'")


def get_globals(*args):
    global _global_dict
    res = [__get_dict(_global_dict, arg.split("|")) for arg in args]
    return res if len(res) > 1 else res[0]


def set_globals(**kwargs):
    global _global_dict
    for kw, value in kwargs.items():
        path = kw.split("|")
        __set_dict(_global_dict, path, value)


def push_message(msg):
    __output_queue.push(msg)


def pop_message():
    return __output_queue.pop()


def can_pop():
    return len(__output_queue) > 0


def register_response_function(func, name, description="No description provided", condition=None,
                               maintenance_state: backend.FunctionMaintenanceState=backend.FunctionMaintenanceState.FUNCTIONAL):
    """
    Registers a specific function in the function dict with a name and
    an optional description (for %help)
    """
    __response_dict[name] = {
        "function": func,
        "description": description,
        "condition": condition,
        "maintenance state": maintenance_state
    }


def get_response_function(name: str):
    """
    Tries to find a function under a given name. If it finds none,
    it executes not_a_respond, which just prints out an error message
    """
    global __response_dict
    if name not in __response_dict:
        return not_a_response
    return __response_dict[name]["function"]


def special_reaction(inp):
    for name, struct in __response_dict.items():
        if struct["condition"] is not None:
            print(struct)
            if struct["condition"](inp):
                return struct["function"]


def register_routine(func, time):
    __routine_list[func.__name__] = (func, time)


def not_a_response(inp):
    return backend.ResponseOutput(inp.args[0] + " is not a valid command", inp.channel)


def update_server_data(server_id, **kwargs):
    """
    updates fields of the server in the database
    """
    servers = get_globals("database_client|executer_database|servers")
    for keyword, value in kwargs.items():
        if keyword in servers.find_one({"discord_id": server_id}):
            servers.update_one({"discord_id": server_id}, {"$set": {keyword: value}}, upsert=True)
        else:
            raise KeyError(f"Error occurred trying to update the database {keyword} not a valid keyword\n")


def restore_client():
    global __client, _global_dict
    intents = Intents.all()
    __client = discord.Client(intents=intents)
    _global_dict["client"] = __client
    return __client
