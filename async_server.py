import asyncio

class Server:

    @asyncio.coroutine
    def handle_client(self, reader, writer):
        data = yield from reader.read(3)
        print(data)

    def start(self, loop):
        self._server = loop.run_until_complete(
            asyncio.start_server(self.handle_client,
                              '127.0.0.1', 2080,
                              loop=loop))
    
    def stop(self, loop): 
        if self._server is not None:
            self._server.close()
            loop.run_until_complete(self._server.wait_closed())
            self._server = None

server = Server()
loop = asyncio.get_event_loop()
server.start(loop)

try:
    loop.run_forever()
except KeyboardInterrupt:
    print('\nQuit..')
server.stop(loop)
loop.close()
