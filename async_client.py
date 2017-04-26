import asyncio

class SomeProtocol(asyncio.Protocol):
    
    def __init__(self, loop):
        self.loop = loop
        
    def connection_made(self, transport):
         

loop = asyncio.get_event_loop()
coro = loop.create_connection(lambda: SomeProtocol(loop), 
                        'www.qq.com', 80)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()


