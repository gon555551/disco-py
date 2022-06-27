import websockets, json, asyncio, queue, typing, threading, requests
from events import *


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

        self.__set_intents()

        self.token: str = token

        self.__queue = queue.Queue()
        self.__intents: int = None
        self.__get_app_id()

    def __set_intents(self) -> None:
        for bit, attr in enumerate(list(self.__annotations__)):
            self.__setattr__(attr, 2**bit)

    @property
    def intents(self) -> int:
        return self.__intents

    @intents.setter
    def intents(self, *args) -> None:
        self.__intents = sum(*args)

    def loop(self) -> None:
        """start the event loop"""
        self.__event_loop = asyncio.get_event_loop()
        self.__event_loop.run_until_complete(self.__establish_connection())

    async def __establish_connection(self):
        async with websockets.connect(
            "wss://gateway.discord.gg/?v=10&encoding=json"
        ) as ws:
            self.ws = ws
            await self.__prepare()
            await self.__listener()

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

        self.__event_loop.create_task(self.__heartbeat())
        threading.Thread(
            target=asyncio.run, args=(self.__gateway_handler(),), daemon=True
        ).start()

        self.__call_on_ready()

    async def __heartbeat(self):
        while True:
            await asyncio.sleep(self.__heartbeat_interval / 1000)
            await self.ws.send(json.dumps({"op": 1, "d": self.__seq}))

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

    def __call_on_ready(self) -> None:
        pass

    def __get_app_id(self) -> None:
        user_url = "https://discord.com/api/v10/users/@me"
        self.__app_id = requests.get(
            user_url, headers={"Authorization": f"Bot {self.token}"}
        ).json()["id"]

    def register(self, json) -> None:
        commands_url = (
            f"https://discord.com/api/v10/applications/{self.__app_id}/commands"
        )
        commands_list = [
            name
            for name in [
                command["name"]
                for command in requests.get(
                    commands_url, headers={"Authorization": f"Bot {self.token}"}
                ).json()
            ]
        ]
        if json["name"] in commands_list:
            requests.patch(
                commands_url, headers={"Authorization": f"Bot {self.token}"}, json=json
            )
        else:
            requests.post(
                commands_url, headers={"Authorization": f"Bot {self.token}"}, json=json
            )

    async def __listener(self):
        while True:
            if self.ws.closed is True:
                break
            self.__queue.put(json.loads(await self.ws.recv()))
        await self.__resume_protocol()

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
                        await self.__call_on_message_create(self.__event)
                    case "INTERACTION_CREATE":
                        self.__event = InteractionCreate(self.__event)
                        await self.__call_on_interaction_create(self.__event)
                    case _:
                        print(self.__event)

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

    async def __call_on_message_create(self, event: MessageCreate) -> None:
        pass

    def send_message(self, content: str) -> None:
        """send a message in the channel of the MESSAGE_CREATE event you're responding to

        Args:
            content (str): content of the message
        """

        endpoint_url = (
            f"https://discord.com/api/v10/channels/{self.__event.channel_id}/messages"
        )
        requests.post(
            endpoint_url,
            json={"content": content},
            headers={"Authorization": f"Bot {self.token}"},
        )

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

    async def __call_on_interaction_create(self, event: InteractionCreate) -> None:
        pass

    def send_interaction(self, content: str) -> None:
        """respond to an interaction

        Args:
            content (str): content of the response
        """

        endpoint_url = f"https://discord.com/api/v10/interactions/{self.__event.id}/{self.__event.token}/callback"
        requests.post(endpoint_url, json={"type": 4, "data": {"content": content}})
