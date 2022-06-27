import websockets, json, asyncio, queue, threading, typing


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
        self.__set_intents()

        self.token: str = token

        self.__queue = queue.Queue()
        self.__intents: int = None

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
        threading.Thread(target=self.__gateway_handler, daemon=True).start()

        self.__call_on_ready()

    async def __heartbeat(self):
        while True:
            await asyncio.sleep(self.__heartbeat_interval / 1000)
            await self.ws.send(json.dumps({"op": 1, "d": self.__seq}))

    def on_ready(self) -> typing.Callable[[], None]:
        def __on_ready(
            call_on_ready: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_ready = call_on_ready

        return __on_ready

    def __call_on_ready(self) -> None:
        pass

    async def __listener(self):
        while True:
            self.__queue.put(json.loads(await self.ws.recv()))

    def __gateway_handler(self):
        while True:
            if not self.__queue.empty():
                event: dict = self.__queue.get(block=False)
                match event["t"]:
                    case "MESSAGE_CREATE":
                        self.__call_on_message_create(MessageCreate(event))
                    case _:
                        print(event)

    def message_create(self) -> typing.Callable[[], None]:
        def __on_message_create(
            handler_function: typing.Callable[[], None]
        ) -> typing.Callable[[], None]:
            self.__call_on_message_create = handler_function

        return __on_message_create

    def __call_on_message_create(self, _) -> None:
        pass


class MessageCreate:
    channel_id: str
    timestamp: str
    member: dict
    content: str
    author: dict
    guild_id: str

    def __init__(self, event: dict) -> None:
        self.event = event
        self.__set_message_attributes()

    def __set_message_attributes(self) -> None:
        for attr in self.__annotations__:
            self.__setattr__(attr, self.event["d"][attr])
