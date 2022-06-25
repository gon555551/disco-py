import websockets, asyncio, json, dataclasses, register

@dataclasses.dataclass
class Info:
    d: int
    sid: str

# heartbeat coroutine
async def heartbeat(ws: websockets.WebSocketClientProtocol, hb: int, d: Info):
    while True:
        await asyncio.sleep(hb/1000)
        await ws.send(json.dumps(
            {
                'op': 1,
                'd': d.d
            }
        ))
        print('BA-DUM')

# basic setup
async def start(ws: websockets.WebSocketClientProtocol, d: Info, loop: asyncio.AbstractEventLoop):
    op10 = json.loads(await ws.recv())
    hb: int = op10['d']['heartbeat_interval']
    op1 = json.dumps(
        {
            'op': 1,
            'd': op10['s']
        }
    )
    await ws.send(op1)
    loop.create_task(heartbeat(ws, hb, d))

    await ws.recv()
    op2 = json.dumps(
        {
            'op': 2,
            'd': {
                'intents': 8,
                'token': 'OTc2ODkwMzExMDUxNzI2ODU5.GLfLQJ.2FrH0usmyLFgphww5pe9GleZ402XE14ptjaSOU',
                'properties': {
                    'os': 'linux',
                    'browser': 'disco',
                    'device': 'disco'
                }
            }
        }
    )
    await ws.send(op2)
    op0 = json.loads(await ws.recv())
    d.d = op0['s']
    d.sid = op0['d']['session_id']
    print(f"{op0['d']['user']['username']} ready with sid {d.sid}")


# listener
async def listen(ws: websockets.WebSocketClientProtocol, d: Info, loop: asyncio.AbstractEventLoop):
    while True:
        msg = json.loads(await ws.recv())
        print(msg)
        match msg['op']:
            case 1:
                await ws.send(json.dumps(
                    {
                        'op': 1,
                        'd': d.d
                    }
                ))
            case 0:
                d.d = msg['s']
                if msg['t'] == 'INTERACTION_CREATE':
                    if msg['d']['data']['options'][0]['value'] == 'animal_dog':
                        js ={
                                'type': 4,
                                'data': {
                                    'content': 'dog POGGERS',
                                }
                            }
                        register.send(js, msg['d']['id'], msg['d']['token'])
            case _:
                d.d = msg['s']


# main
async def main(loop: asyncio.AbstractEventLoop):
    d = Info(0, '')
    # register.register()
    # print('registered')

    async with websockets.connect('wss://gateway.discord.gg/?v=10&encoding=json') as ws:
        await start(ws, d, loop)
        await listen(ws, d, loop)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
