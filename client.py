import websockets
import requests
import asyncio
import json


class Client:
    ws: websockets.WebSocketClientProtocol  # typehints don't work
    s: int
    id: str
    hb: int
    intents: int
    name: str
    appid: str
    auth_headers: dict

    _loop: asyncio.AbstractEventLoop
    _commands: dict
    _handlers: list

    message: str
    handling: dict

    def __init__(self, token: str, intents: int) -> None:
        self._commands = dict()
        self._handlers = dict()
        self.token = token
        self.intents = intents

        id_url = "https://discord.com/api/v10/oauth2/applications/@me"
        self.auth_headers = {"Authorization": f"Bot {self.token}"}
        self.appid = requests.get(id_url, headers=self.auth_headers).json()["id"]

    def go_online(self) -> None:
        self.s, self.id, self._loop = (
            int(),
            str(),
            asyncio.get_event_loop(),
        )

        register_url = f"https://discord.com/api/v10/applications/{self.appid}/commands"
        for app_comms in requests.get(register_url, headers=self.auth_headers).json():
            if app_comms["name"] not in self._commands:
                requests.delete(
                    f"https://discord.com/api/v10/applications/{self.appid}/commands/{app_comms['id']}",
                    headers=self.auth_headers,
                )

        self.__register_commands()

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

    # on ready decorator
    def on_ready(self, func):
        self.__call_on_ready = func

    def __call_on_ready(self):
        pass

    def slash_command(self, func):
        json = func(False)
        self._commands[json["name"]] = json

        async def full_handler(handle: bool):
            func(handle)
            callback_url = f"https://discord.com/api/v10/interactions/{self.handling['id']}/{self.handling['token']}/callback"
            requests.post(
                callback_url,
                json={"type": 4, "data": {"content": self.message}},
            )
            self.message = None

        self._handlers[json["name"]] = full_handler

    def __register_commands(self):
        register_url = f"https://discord.com/api/v10/applications/{self.appid}/commands"
        names = []
        for already_in in requests.get(register_url, headers=self.auth_headers).json():
            names.append(already_in["name"])

        for json in self._commands.values():
            if json["name"] in names:
                requests.patch(register_url, headers=self.auth_headers, json=json)
            else:
                print(f'posted {json["name"]}')
                requests.post(register_url, headers=self.auth_headers, json=json)

    # event listener
    async def __listener(self) -> None:
        while True:
            if self.ws.closed is True:
                self.resume()

            msg = json.loads(await self.ws.recv())
            self.handling = msg["d"]
            match msg["op"]:
                case 1:
                    self.s = msg["s"]
                    await self.ws.send(json.dumps({"op": 1, "d": self.s}))
                case 0:
                    self.s = msg["s"]
                    if msg["d"]["data"]["name"] in self._handlers.keys():
                        await self._handlers[self.handling["data"]["name"]](True)
                case _:
                    self.s = msg["s"]

    # resuming protocol
    async def resume(self) -> None:
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
                            "session_id": self.id,
                            "seq": self.s,
                        },
                    }
                )
            )

            await self.__listener()
