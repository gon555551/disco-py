import websockets, asyncio, threading, requests, json, queue, typing, multipledispatch
from events import *
from errors import *


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

        self.__get_app_id()
        self.__set_intents()
        self.__intents: int = None
        self.__command_dict = dict()
        self.__queue = queue.Queue()

    # gets the app id for the bot
    def __get_app_id(self) -> None:
        user_url = "https://discord.com/api/v10/users/@me"
        self.__app_id = requests.get(
            user_url, headers={"Authorization": f"Bot {self.token}"}
        ).json()["id"]

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
        async with websockets.connect(
            "wss://gateway.discord.gg/?v=10&encoding=json"
        ) as ws:
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
        async with websockets.connect(
            "wss://gateway.discord.gg/?v=10&encoding=json"
        ) as ws:
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
        commands_url = (
            f"https://discord.com/api/v10/applications/{self.__app_id}/commands"
        )
        for commands in requests.get(
            commands_url, headers={"Authorization": f"Bot {self.token}"}
        ).json():
            self.__command_dict[commands["name"]] = commands["id"]

    #
    # from here on, independent methods that the user calls directly
    #
    # register an application command
    def register(self, json) -> None:
        """register a slash command

        Args:
            json (_type_): slash command json
        """

        self.__get_command_dict()
        commands_url = (
            f"https://discord.com/api/v10/applications/{self.__app_id}/commands"
        )
        if json["name"] in self.__command_dict.keys():
            requests.patch(
                f"{commands_url}/{self.__command_dict[json['name']]}",
                headers={"Authorization": f"Bot {self.token}"},
                json=json,
            )
        else:
            requests.post(
                commands_url, headers={"Authorization": f"Bot {self.token}"}, json=json
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
        commands_url = (
            f"https://discord.com/api/v10/applications/{self.__app_id}/commands"
        )
        if name in self.__command_dict.keys():
            requests.delete(
                f"{commands_url}/{self.__command_dict[name]}",
                headers={"Authorization": f"Bot {self.token}"},
            )
        else:
            raise CommandMissing(name)

    # delete all application commands
    def clean(self):
        """delete all slash commands"""

        self.__get_command_dict()
        commands_url = (
            f"https://discord.com/api/v10/applications/{self.__app_id}/commands"
        )
        for command_id in self.__command_dict.values():
            requests.delete(
                f"{commands_url}/{command_id}",
                headers={"Authorization": f"Bot {self.token}"},
            )

    # send a message in response to an event
    @multipledispatch.dispatch(str)
    def send_message(self, content: str) -> None:
        """send a message in the channel of the MESSAGE_CREATE event you're responding to

        Args:
            content (str): content of the message
        """

        self.__event: MessageCreate

        endpoint_url = (
            f"https://discord.com/api/v10/channels/{self.__event.channel_id}/messages"
        )
        requests.post(
            endpoint_url,
            json={"content": content},
            headers={"Authorization": f"Bot {self.token}"},
        )

    # sends a message to a specific channel
    @multipledispatch.dispatch(str, str)
    def send_message(self, content: str, channel_id: str) -> None:
        """send a message in the channel of the MESSAGE_CREATE event you're responding to

        Args:
            content (str): content of the message
            channel_id (str): the id of the channel to send the message in
        """

        self.__event: MessageCreate

        endpoint_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        requests.post(
            endpoint_url,
            json={"content": content},
            headers={"Authorization": f"Bot {self.token}"},
        )

    # ack an interaction
    @multipledispatch.dispatch()
    def send_interaction(self) -> None:
        """send a PONG to a PING"""

        self.__event: InteractionCreate

        endpoint_url = f"https://discord.com/api/v10/interactions/{self.__event.id}/{self.__event.token}/callback"

        requests.post(endpoint_url, json={"type": 1})

    # respond to an interaction with a message
    @multipledispatch.dispatch(str, bool)
    def send_interaction(self, content: str, ephemeral: bool = False) -> None:
        """send an interaction response

        Args:
            content (str): the content of the message
            ephemeral (bool, optional): whether it's an ephemeral. Defaults to False.
        """

        self.__event: InteractionCreate

        endpoint_url = f"https://discord.com/api/v10/interactions/{self.__event.id}/{self.__event.token}/callback"
        if ephemeral:
            json = {"type": 4, "data": {"content": content, "flags": 64}}
        else:
            json = {"type": 4, "data": {"content": content}}

        requests.post(endpoint_url, json=json)

    # send a DM to a user while responding to an event
    @multipledispatch.dispatch(str)
    def send_dm(self, content: str) -> None:
        """sends a DM to a user

        Args:
            content (str): the content of the DM
        """

        endpoint_url = "https://discord.com/api/v10/users/@me/channels"
        dm_channel = requests.post(
            endpoint_url,
            headers={"Authorization": f"Bot {self.token}"},
            json={"recipient_id": self.__event.author["id"]},
        ).json()
        send_url = f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages"
        requests.post(
            send_url,
            json={"content": content},
            headers={"Authorization": f"Bot {self.token}"},
        )

    # send a DM to a specific user
    @multipledispatch.dispatch(str, str)
    def send_dm(self, content: str, user_id: str) -> None:
        """sends a DM to a user

        Args:
            content (str): the content of the DM
            user_id (str): the id of the user to send it to
        """

        endpoint_url = "https://discord.com/api/v10/users/@me/channels"
        dm_channel = requests.post(
            endpoint_url,
            headers={"Authorization": f"Bot {self.token}"},
            json={"recipient_id": user_id},
        ).json()
        send_url = f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages"
        requests.post(
            send_url,
            json={"content": content},
            headers={"Authorization": f"Bot {self.token}"},
        )

    # reply to a message with a message
    def reply(self, content: str, mention: bool = True):
        """sends a message reply

        Args:
            content (str): the content of the message
            mention (bool, optional): whether to mention the user. Defaults to True.
        """

        endpoint_url = (
            f"https://discord.com/api/v10/channels/{self.__event.channel_id}/messages"
        )
        requests.post(
            endpoint_url,
            headers={"Authorization": f"Bot {self.token}"},
            json={
                "content": content,
                "message_reference": {"message_id": self.__event.id},
                "allowed_mentions": {"replied_user": mention},
            },
        )
