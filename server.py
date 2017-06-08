import socket
import struct
import asyncio 
import logging
from errno import ENETUNREACH, EHOSTUNREACH, ECONNREFUSED

from server_protocol import ServerClientProtocol
from logger import console_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

loop = asyncio.get_event_loop()
coro = loop.create_server(ServerClientProtocol, '127.0.0.1', 1080)
server = loop.run_until_complete(coro)
logger.info('Asock server started at 127.0.0.1:1080')

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

logger.info('Shutting down Asock server...')
server.close()
loop.run_until_complete(server.wait_closed())

logger.info('Shutting down event loop...')
loop.close()

