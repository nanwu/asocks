import sys
import asyncio
import errno
import struct
import logging
import socket
import functools

import auth
from networking import (SOCK_PROTOCOL_VERSION, AddressType, 
                        ConnectionStatus as Status)
from exception import InvalidRequest, WrongProtocol, ConnectToRemoteError
from config import *
from logger import console_handler


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

class Socks5ProtocolState:
    
    INIT = 0
    NEGOTIATED = 1
    AUTHORIZED = 2
    CONNECTED = 3

    StateMapping = None

    @classmethod
    def get_state(cls, state):
        if cls.StateMapping is None:
            cls.StateMapping = {
                getattr(cls, attr): attr 
                for attr in dir(cls) 
                if not callable(getattr(cls, attr))
                and not attr.startswith('__') and attr != 'StateMapping'}

        return cls.StateMapping.get(state)
     
class ServerRemoteProtocol(asyncio.Protocol):
    
    def __init__(self, transport_to_client):
        self.transport_to_remote = None
        self.transport_to_client = transport_to_client

    def connection_made(self, transport):
        self.transport_to_remote = transport

    def data_received(self, data):
        self.transport_to_client.write(data)

class ServerClientProtocol(asyncio.Protocol):
    
    def __init__(self):
        self.transport_to_client = None
        self.transport_to_remote = None
        self.remote_host_atype = None
        self._loop = None

        self.state = Socks5ProtocolState.INIT

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)

    def _next_state(self, skips=0):
        """ Move protocol state forward by one plus skips"""
        self.state += 1 + skips

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.logger.info('Receives connection from {}.'.format(peername))

        self.transport_to_client = transport
        self._loop = self.transport_to_client._loop

    def data_received(self, data):
        self.logger.info('CURRENT STATE:{}'.format(
            Socks5ProtocolState.get_state(self.state)))
        self.logger.info(str(data))
             
        if self.state == Socks5ProtocolState.INIT:
            self._negotiate_auth_method(data)
        elif self.state == Socks5ProtocolState.NEGOTIATED:
            raise NotImplementedError
        elif self.state == Socks5ProtocolState.AUTHORIZED:
            self._accept_connect(data)
        elif self.state == Socks5ProtocolState.CONNECTED:
            self._tunneling(data)
            
    def _negotiate_auth_method(self, data):
        if len(data) <= 2:
            raise InvalidRequest

        if data[0] != 5:
            raise WrongProtocol

        auth_method_count = data[1] 
        auth_method_codes = data[2:]
        if len(auth_method_codes) < auth_method_count:
            raise InvalidRequest

        # If not method selected. Connection will close. 
        accepted_code = b'\xff' 

        for auth_method_code in auth_method_codes:
            if auth_method_code in auth.acceptable_auth_method_codes:
                accepted_code = struct.pack(">B", auth_method_code)
                break
        
        response = b'\x05' + accepted_code
        self.transport_to_client.write(response)
        if accepted_code == b'xff':
            self.transport_to_client.close()
        else: 
            # Skip auth phase if not required
            accepted_code = struct.unpack('>B', accepted_code)[0]
            self._next_state(accepted_code == auth.NoAuthRequired.method_code)

    def _accept_connect(self, data):
        version = data[0] 
        assert version == SOCK_PROTOCOL_VERSION 

        cmd = data[1]
        assert cmd == 1

        self.remote_host_atype = atype = data[3:4]
        atype = struct.unpack('>B', atype)[0]
        assert atype in (1, 3, 4) 
        if atype == AddressType.IPv6:
            host = '.'.join([str(byte) for byte in data[4:8]])
            port = data[8:10]
        elif atype == AddressType.DomainName:
            addr_octets_count = data[4]
            host = data[5:5+addr_octets_count]
            port = data[5+addr_octets_count:7+addr_octets_count]
        else:
            assert len(data) > 22
            host = ':'.join(
                [str(struct.unpack('>H', data[idx:idx+2])[0]) 
                 for idx in range(4, 20, 2)])
            port = data[20:22]

        port = struct.unpack('>H', port)[0]
        self.logger.info(
	        'Connecting to remove server at {}:{}.'.format(host, port))

        waiter = asyncio.Future()
        waiter.add_done_callback(self._remote_connected)
        task = self._loop.create_task(self._connect_to_remote(host, port, waiter)) 
    
    @asyncio.coroutine
    def _connect_to_remote(self, host, port, waiter):
        exception = None
        try:
            transport, protocol = yield from self._loop.create_connection(
                functools.partial(ServerRemoteProtocol, 
                                  transport_to_client=self.transport_to_client),
                host, 
                port,
                local_addr=('10.0.2.15', PORT_CONNECT_REMOTE))
        except socket.timeout:
            reply = Status.TTL_EXPIRED
            waiter.set_exception(ConnectToRemoteError(reply))
        except socket.error as err:
            if err.errno == errno.ENETUNREACH:
                reply = Status.NETWORK_UNREACHABLE
            elif err.errno == errno.EHOSTUNREACH:
                reply = Status.HOST_UNREACHABLE
            elif err.errno == errno.ECONNREFUSED:
                reply = Status.CONN_REFUSED
            else:
                reply = socket.error 
            waiter.set_exception(ConnectToRemoteError(reply))
            self.logger.error(
		        'Connecting to {}:{} failed. Error code:{}'.format(
		        host, port, reply))
        except:
            reply = Status.GENERAL_FAIL
            waiter.set_exception(ConnectToRemoteError(reply))
            self.logger.error('Connecting to {}:{} failed.'.format(host, port))
        else:
            self.logger.error('Connected to {}:{}.'.format(host, port))
            waiter.set_result((transport, protocol))

    def _remote_connected(self, future):
        try:
            self.transport_to_remote = future.result()[0]
        except ConnectToRemoteError as exc:
            reply = struct.pack('>B', exc.args[0])
        else:
            reply = b'\x00'   
        
        response_to_client = [
            b'\x05', # protocol version
            reply,   
            b'\x00',  
	        self.remote_host_atype,
            b'\x00', 
            b'\x00'
        ] 
        response_to_client = b''.join(response_to_client)
        self.transport_to_client.write(response_to_client)
        if reply != b'\x00':
            self.transport_to_client.close() # triggers connection_lost()

    def connection_lost(self):
        """Need to clean up connection with remote host here"""
        self.logger.info('Closing connection')
        self.transport_to_remote.close()

    def _tunneling(self, data):
        self.transport_to_remote.write(data)
        
          
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
