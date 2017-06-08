import socket
import struct
import asyncio 
import argparse
import logging
from errno import ENETUNREACH, EHOSTUNREACH, ECONNREFUSED

from server.server_protocol import ServerClientProtocol
from logger import console_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

def start_serve(*args, **kwargs):
    loop = asyncio.get_event_loop()
    coro = loop.create_server(
        protocol_factory=ServerClientProtocol, 
        host=kwargs['addr'],
        port=kwargs['port'], 
        backlog=kwargs['concurrency'])

    server = loop.run_until_complete(coro)
    logger.info(
        'Asock server starts listening at {}:{}'.format(
            kwargs['addr'], kwargs['port']))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())

    logger.info('Shutting down eventloop.')
    loop.close()
    logger.info('Shutting down Asocks proxy service.')

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', '--port', type=int, 
        help='specify the port proxy server listens on')
    arg_parser.add_argument('-c', '--concurrency', type=int,
        help='max concurrent connections server will accept')
    arg_parser.add_argument('-l', '--local', action='store_true',
        help='running server on localhost')
    args = arg_parser.parse_args()
    
    proxy_port = args.port or 1080
    concurrency = args.concurrency or 256
    addr = '127.0.0.1' if args.local else '0.0.0.0'
    
    kwargs = {'addr': addr,
              'port': proxy_port,
              'concurrency': concurrency}
    start_serve(**kwargs)

if __name__ == '__main__':
    main()
