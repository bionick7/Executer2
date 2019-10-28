import discord

from io import BytesIO
from os import path
from PIL import Image
from enum import Enum
from functools import wraps
from sys import stdout

default_guild = None
default_channel = None
default_author = None
default_message = None


class ResponseOutput:
    def __init__(self, *args):
        self.valid = True
        if isinstance(args[0], str):
            self.message = args[0]
            self.embed = None
            if args[0] == "":
                self.valid = False
        elif isinstance(args[0], discord.Embed):
            self.message = ""
            self.embed = args[0]
        else:
            self.message, self.embed = "", None
            self.valid = False

        if isinstance(args[1], (discord.DMChannel, discord.TextChannel, discord.GroupChannel)):
            self.channel = args[1]
            self.user_message = None
        elif isinstance(args[1], (discord.User, discord.Member)):
            self.channel = None
            self.user_message = args[1]
        else:
            self.channel, self.user_message = None, None
            self.valid = False

        self.files = []

    def add_file_from_path(self, path_):
        if path.exists(path_):
            with open(path_, "rb") as file_data:
                self.files.append(discord.File(file_data, path_))

    def add_text_file(self, text, filename="text.txt", encoding="UTF-8"):
        buffer = text.encode(encoding)
        self.files.append(discord.File(buffer, filename))

    def add_image(self, image, name="image.png"):
        buffer = BytesIO
        image.save(buffer, format="PNG")
        self.files.append(discord.File(buffer, name))

    async def post(self):
        if not self.valid:
            return
        channel = self.channel
        if channel is None and self.user_message is not None:
            channel = self.user_message.dm_channel
            if channel is None:
                await self.user_message.create_dm()
                channel = self.user_message.dm_channel
        await channel.send(self.message, embed=self.embed, files=self.files)


class ResponseInput:
    def __init__(self, *args):
        self.text = ""
        if isinstance(args[0], str):
            self.__init_text(*args)
        elif isinstance(args[0], discord.Message):
            self.__init_message(*args)
        self.command, self.request_delete = False, False
        self.args, self.kwargs = [], {}
        self.content_text = ""
        self.__update_args()

    def __init_text(self, text_string, data):
        self.data = data
        self.raw_message = default_message
        self.channel = default_channel
        self.guild = default_guild
        self.author = default_author

        self.text = text_string

    def __init_message(self, discord_message: discord.Message, data):
        self.data = data
        self.raw_message = discord_message
        self.channel = discord_message.channel
        self.guild = discord_message.guild
        self.author = discord_message.author

        self.text = discord_message.content

    def __update_args(self):
        self.args.clear()
        self.kwargs.clear()
        for a in self.text.split(" "):
            if "=" in a:
                key, value = a.split("=")[0:2]
                self.kwargs[key] = value
            else:
                self.args.append(a)
        if not self.args:
            self.args = [self.text]
        try:
            self.content_text = self.text[len(self.args[0]):]  # something wrong here
        except IndexError:
            print("Index error at 62 / args[0]: {0} text: {1}".format(self.args[0], self.text))

    def check(self):
        prefix, delete_prefix = self.data["general"]["prefix"], self.data["general"]["delete prefix"]
        if self.text.startswith(prefix):
            self.command = True
            self.text = self.text[len(prefix):]
            if self.text.startswith(delete_prefix):
                self.request_delete = True
                self.text = self.text[len(delete_prefix):]
            self.__update_args()

    async def get_images(self):
        image_list = []
        for attachment in self.raw_message.attachments:
            if attachment.filename.endswith(".png"):
                image_list.append(Image.open(BytesIO(await attachment.read())))
        return image_list

    async def get_raw_attachment(self):
        byte_array = []
        for attachment in self.raw_message.attachments:
            byte_array.append(Image.open(await attachment.read()))
        return byte_array


class Queue:
    def __init__(self):
        self.__content = []

    def push(self, item):
        self.__content.append(item)

    def pop(self):
        return self.__content.pop(0)

    def __len__(self):
        return len(self.__content)


class FunctionMaintenanceState(Enum):
    FUNCTIONAL = 0
    LEGACY = 1
    OUTDATED = 2
    NOT_IMPLEMENTED = 3

    
def document(loading_not, finish_not):
    def decorator_repeat(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stdout.write(loading_not + " " * min(0, 100 - len(loading_not)))
            stdout.flush()
            func(*args, **kwargs)
            stdout.write(finish_not + "\n")
        return wrapper
    return decorator_repeat
