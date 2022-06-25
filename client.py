import websockets
import asyncio
import json


class Client:
    ws: websockets.WebSocketClientProtocol  # typehints don't work
    s: int
    id: str
    hb: int
    intents: int
    name: str

    _loop: asyncio.AbstractEventLoop

    def go_online(self, token: str, intents: int) -> None:
        self.s, self.id, self.token, self._loop = (
            int(),
            str(),
            token,
            asyncio.get_event_loop(),
        )

        # should make conversion from text to int
        self.intents = intents

        # NEED TO REGISTER COMMANDS HERE
        #

        self._loop.run_until_complete(self.__establish_websocket_gateway())

    # establish the wesocket gateway connection
    async def __establish_websocket_gateway(self) -> None:
        async with websockets.connect(
            "wss://gateway.discord.gg/?v=10&encoding=json"
        ) as ws:
            self.ws = ws
            await self.__ready_client()
            await self.__listener()

    # heartbeat method
    async def __heartbeat(self) -> None:
        while True:
            await asyncio.sleep(self.hb / 1000)
            await self.ws.send(json.dumps({"op": 1, "d": self.s}))

    # initiation procedure
    async def __ready_client(self) -> None:
        op10 = json.loads(await self.ws.recv())
        self.hb = op10["d"]["heartbeat_interval"]
        op1 = json.dumps({"op": 1, "d": op10["s"]})
        await self.ws.send(op1)
        self._loop.create_task(self.__heartbeat())
        await self.ws.recv()

        op2 = json.dumps(
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
        await self.ws.send(op2)
        op0 = json.loads(await self.ws.recv())
        self.s = op0["s"]
        self.id = op0["d"]["session_id"]
        self.name = op0["d"]["user"]["username"]

        self.__call_on_ready()

    # event listener
    async def __listener(self) -> None:
        while True:
            msg = json.loads(await self.ws.recv())
            match msg["op"]:
                case 1:
                    await self.ws.send(json.dumps({"op": 1, "d": self.s}))
                case _:
                    self.s = msg["s"]

    # on ready decorator
    def on_ready(self, func):
        self.__call_on_ready = func

    def __call_on_ready(self):
        pass
