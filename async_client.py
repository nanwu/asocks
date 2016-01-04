import asyncio

@asyncio.coroutine
def client(loop):
    r, w = yield from asyncio.open_connection(
        '127.0.0.1', 2080,
        loop=loop)
    w.write(b'\x05\x01\x00')
    yield from w.drain()
    data = yield from r.readline() 
    print(data)
    w.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(client(loop))
loop.close()
