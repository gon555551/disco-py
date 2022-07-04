import websockets
import threading
import requests
import asyncio
import typing
import queue
import json
from utilities.endpoints import *
from utilities.obj_util import *
from utilities.builder import *
from utilities.events import *
from utilities.errors import *


class Bot:
    GUILDS: int
    GUILD_MEMBERS: int
    GUILD_BANS: int
    GUILD_EMOJIS_AND_STICKERS: int
    GUILD_INTEGRATIONS: int
    GUILD_WEBHOOKS: int
    GUILD_INVITES: int
    GUILD_VOICE_STATES: int
    GUILD_PRESENCES: int
    GUILD_MESSAGES: int
    GUILD_MESSAGE_REACTIONS: int
    GUILD_MESSAGE_TYPING: int
    DIRECT_MESSAGES: int
    DIRECT_MESSAGE_REACTIONS: int
    DIRECT_MESSAGE_TYPING: int
    MESSAGE_CONTENT: int
    GUILD_SCHEDULED_EVENTS: int
    AUTO_MODERATION_CONFIGURATION: int
    AUTO_MODERATION_EXECUTION: int

    def __init__(self, token: str) -> None:
        """your bot

        Args:
            token (str): your bot token
        """

        self.token: str = token
        self.__auth: dict = {"Authorization": f"Bot {self.token}"}

        self.__get_app_id()
        self.__set_intents()
        self.__intents: int = None
        self.__command_dict = dict()
        self.__queue = queue.Queue()

    # gets the app id for the bot
    def __get_app_id(self) -> None:
        self.__app_id = requests.get(user_endpoint, headers=self.__auth).json()["id"]
        self.__commands_url = app_commands_end(self.__app_id)

    # sets the int for each bot intent
    def __set_intents(self) -> None:
        for bit, attr in enumerate(list(self.__annotations__)):
            self.__setattr__(attr, 2**bit)

    # intents property, so the user can select the intents
    @property
    def intents(self) -> int:
        return self.__intents

    # setter for intents
    @intents.setter
    def intents(self, *args) -> None:
        self.__intents = sum(*args)

    # start the event loop
    def loop(self) -> None:
        """start the event loop"""
        self.__event_loop = asyncio.get_event_loop()
        self.__event_loop.run_until_complete(self.__establish_connection())

    # async method for establishing the websocket connection
    async def __establish_connection(self):
        async with websockets.connect(gateway_url) as ws:
            self.ws = ws
            await self.__prepare()
            await self.__listener()

    # connecting sequence with heartbeat and identify
    async def __prepare(self):
        hello = json.loads(await self.ws.recv())
        self.__heartbeat_interval = hello["d"]["heartbeat_interval"]

        first_heartbeat = json.dumps({"op": 1, "d": None})
        await self.ws.send(first_heartbeat)
        await self.ws.recv()

        identify = json.dumps(
            {
                "op": 2,
                "d": {
                    "intents": self.intents,
                    "token": self.token,
                    "properties": {
                        "os": "linux",
                        "browser": "disco",
                        "device": "disco",
                    },
                },
            }
        )
        await self.ws.send(identify)
        ready = json.loads(await self.ws.recv())
        self.__seq = ready["s"]
        self.__session_id = ready["d"]["session_id"]

        self.username = ready["d"]["user"]["username"]
        self.discriminator = ready["d"]["user"]["discriminator"]
        self.full_name = f"{self.username}#{self.discriminator}"

        self.__call_on_ready()

        self.__event_loop.create_task(self.__heartbeat())
        threading.Thread(
            target=asyncio.run, args=(self.__gateway_handler(),), daemon=True
        ).start()

    # decorator function to call on ready
    def on_ready(self) -> typing.Callable[[], None]:
        """decorator for when the bot completes connecting procedures

        Returns:
            typing.Callable[[], None]: wrapper
        """

        def __on_ready(
            call_on_ready: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_ready = call_on_ready

        return __on_ready

    # by default, call nothing on ready, is changed by self.on_ready()
    def __call_on_ready(self) -> None:
        pass

    # heathbeat loop, used as a task
    async def __heartbeat(self):
        while True:
            await asyncio.sleep(self.__heartbeat_interval / 1000)
            await self.ws.send(json.dumps({"op": 1, "d": self.__seq}))

    # gateway event handler
    async def __gateway_handler(self):
        while True:
            if not self.__queue.empty():
                self.__event: dict = self.__queue.get()
                self.__seq = self.__event["s"]

                if self.__event["op"] == 1:
                    await self.ws.send(json.dumps({"op": 1, "d": self.__seq}))
                    continue

                match self.__event["t"]:
                    case "MESSAGE_CREATE":
                        self.__event = MessageCreate(self.__event)
                        self.__call_on_message_create(self.__event)
                    case "MESSAGE_DELETE":
                        self.__event = MessageDelete(self.__event)
                        self.__call_on_message_delete(self.__event)
                    case "INTERACTION_CREATE":
                        self.__event = InteractionCreate(self.__event)
                        self.__call_on_interaction_create(self.__event)
                    case None:
                        pass
                    case _:
                        print(self.__event)

    # message create decorator, to say it's to respond to a MESSAGE_CREATE event
    def message_create(self) -> typing.Callable[[], None]:
        """decorator for responding to MESSAGE_CREATE events

        Returns:
            typing.Callable[[], None]: wrapper
        """

        def __on_message_create(
            handler_function: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_message_create = handler_function

        return __on_message_create

    # by default do nothing, is changed by self.message_create()
    def __call_on_message_create(self, event: MessageCreate) -> None:
        pass

    # message delete decorator, to say it's to respond to an MESSAGE_DELETE event
    def message_delete(self) -> typing.Callable[[], None]:
        """decorator for responding to MESSAGE_DELETE events

        Returns:
            typing.Callable[[], None]: wrapper
        """

        def __on_message_delete(
            handler_function: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_message_delete = handler_function

        return __on_message_delete

    # by default do nothing, is changed by self.message_delete()
    def __call_on_message_delete(self, event: MessageDelete) -> None:
        pass

    # interaction create decorator, to say it's to respond to an INTERACTION_CREATE event
    def interaction_create(self) -> typing.Callable[[], None]:
        """decorator for responding to INTERACTION_CREATE events

        Returns:
            typing.Callable[[], None]: wrapper
        """

        def __on_interaction_create(
            handler_function: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_interaction_create = handler_function

        return __on_interaction_create

    # by default do nothing, is changed by self.interaction_create()
    def __call_on_interaction_create(self, event: InteractionCreate) -> None:
        pass

    # listener event loop
    async def __listener(self):
        while True:
            if self.ws.closed is True:
                break
            self.__queue.put(json.loads(await self.ws.recv()))
        await self.__resume_protocol()

    # when the connection goes down, enact this protocol
    async def __resume_protocol(self):
        self.ws.close()
        async with websockets.connect(gateway_url) as ws:
            self.ws = ws
            await self.ws.send(
                json.dumps(
                    {
                        "op": 6,
                        "d": {
                            "token": self.token,
                            "session_id": self.__session_id,
                            "seq": self.__seq,
                        },
                    }
                )
            )
            await self.__listener()

    # gets all currently active application commands
    def __get_command_dict(self) -> None:
        for commands in requests.get(self.__commands_url, headers=self.__auth).json():
            self.__command_dict[commands["name"]] = commands["id"]

    #
    # from here on, independent methods that the user calls directly
    #
    # register an application command
    def register(self, *commands: dict) -> None:
        """register a slash command

        Args:
            *commands (dict): slash command json(s)
        """

        self.__get_command_dict()
        for json in commands:
            if json["name"] in self.__command_dict.keys():
                requests.patch(
                    f"{self.__commands_url}/{self.__command_dict[json['name']]}",
                    headers=self.__auth,
                    json=json,
                )
            else:
                requests.post(
                    self.__commands_url,
                    headers=self.__auth,
                    json=json,
                )

    # delete an application command, by name
    def delete(self, name: str):
        """delete a slash command

        Args:
            name (str): the name of the command to delete

        Raises:
            CommandMissing: raised if the command isn't at the endpoint
        """

        self.__get_command_dict()
        if name in self.__command_dict.keys():
            requests.delete(
                f"{self.__commands_url}/{self.__command_dict[name]}",
                headers=self.__auth,
            )
        else:
            raise CommandMissing(name)

    # delete all application commands
    def clean(self):
        """delete all slash commands"""

        self.__get_command_dict()
        for command_id in self.__command_dict.values():
            requests.delete(
                f"{self.__commands_url}/{command_id}",
                headers=self.__auth,
            )

    # send a message in response to an event
    def send_message(
        self,
        dm: bool = False,
        content: str = None,
        tts: bool = None,
        embeds: list[dict] = None,
        allowed_mentions: bool = None,
        message_reference: bool = None,
        components: list = None,
        sticker_ids: list = None,
        flags: int = None,
    ) -> None:
        """sends a message

        Args:
            dm (bool, optional): whether it's a dm. Defaults to False.
            content (str, optional): the content of the message. Defaults to None.
            tts (bool, optional): if the message is tts. Defaults to None.
            embeds (list[dict], optional): the embeds. Defaults to None.
            allowed_mentions (bool, optional): whether it allows mentions. Defaults to None.
            message_reference (bool, optional): whether its a reference. Defaults to None.
            components (list, optional): the message components. Defaults to None.
            sticker_ids (list, optional): the ids of the stickers. Defaults to None.
            flags (int, optional): the flags. Defaults to None.
        """

        if dm is True:
            dm_channel = requests.post(
                dm_endpoint,
                headers=self.__auth,
                json={"recipient_id": self.__event.author.id},
            ).json()
            url = channel_messages_end(dm_channel["id"])
        else:
            url = channel_messages_end(self.__event.channel_id)

        requests.post(
            url,
            json=message_obj(locals(), self.__event.id),
            headers=self.__auth,
        )

    # respond to an interaction with a message
    def send_interaction(self, content: str, ephemeral: bool = False) -> None:
        """send an interaction response

        Args:
            content (str): the content of the message
            ephemeral (bool, optional): whether it's an ephemeral. Defaults to False.
        """

        if ephemeral:
            json = {"type": 4, "data": {"content": content, "flags": 64}}
        else:
            json = {"type": 4, "data": {"content": content}}

        requests.post(
            interactions_callback_end(self.__event.id, self.__event.token), json=json
        )
