import sys
import os
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
from logger import console_handler


class Socks5ProtocolState:
    
    INIT = 0
    NEGOTIATED = 1
    AUTHORIZED = 2
    CONNECTED = 3

    StateMapping = None

    @classmethod
    def state_name(cls, state):
        if cls.StateMapping is None:
            cls.StateMapping = {
                getattr(cls, attr): attr 
                for attr in dir(cls) 
                if not callable(getattr(cls, attr))
                and not attr.startswith('__') and attr != 'StateMapping'}

        return cls.StateMapping.get(state)
     
class ServerRemoteProtocol(asyncio.Protocol):
    """Protocol for streaming to remote host"""
    
    def __init__(self, transport_to_client):
        self.transport_to_remote = None
        self.transport_to_client = transport_to_client
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)

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
        """update protocol state by (1 + #skips)"""
        self.state += 1 + skips

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.logger.info(
            'Received connection from client {}.'.format(peername))

        self.transport_to_client = transport
        self._loop = self.transport_to_client._loop

    def data_received(self, data):

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

        # When no client-proposed auth method is chosen,
        # client connection will be closed. 
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
        if atype == AddressType.IPv4:
            host = '.'.join([str(byte) for byte in data[4:8]])
            port = data[8:10]
        elif atype == AddressType.DomainName:
            addr_octets_count = data[4]
            host = data[5:5+addr_octets_count]
            port = data[5+addr_octets_count:7+addr_octets_count]
        else:
            host = ':'.join(
                [str(struct.unpack('>H', data[idx:idx+2])[0]) 
                 for idx in range(4, 20, 2)])
            port = data[20:22]

        port = struct.unpack('>H', port)[0]
        self.logger.info(
	        'Connecting to remote server at {}:{}.'.format(host, port))

        waiter = asyncio.Future()
        waiter.add_done_callback(self._remote_connected)

        if sys.version_info >= (3, 4, 2):
            # create_task added to asyncio in Python 3.4.2
            task = self._loop.create_task(self._connect_to_remote(host, port, waiter)) 
        else:
            task = asyncio.async(self._connect_to_remote(host, port, waiter))
    
    @asyncio.coroutine
    def _connect_to_remote(self, host, port, waiter):
        exception = None
        try:
            transport, protocol = yield from self._loop.create_connection(
                functools.partial(ServerRemoteProtocol, 
                                  transport_to_client=self.transport_to_client),
                host, 
                port)
        except OSError as err:
            if err.errno == errno.ENETUNREACH:
                reply = Status.NETWORK_UNREACHABLE
            elif err.errno == errno.EHOSTUNREACH:
                reply = Status.HOST_UNREACHABLE
            elif err.errno == errno.ECONNREFUSED:
                reply = Status.CONN_REFUSED
            elif err.errno == errno.ETIMEDOUT:
                reply = Status.TTL_EXPIRED
            else:
                reply = Status.GENERAL_FAIL 

            waiter.set_exception(ConnectToRemoteError(reply))
            self.logger.error('Connecting to {}:{} failed: '.format(
		                  host, port, os.strerror(err.errno)))
        except Exception as e:
            self.logger.error(str(e))
            reply = Status.GENERAL_FAIL
            waiter.set_exception(ConnectToRemoteError(reply))
            self.logger.error('Connecting to {}:{} failed.'.format(host, port))
        else:
            self.logger.info('Connected to {}:{}.'.format(host, port))
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
            # Return empty bndaddr and bndport to client
            struct.pack('B', AddressType.DomainName),
            b'\x00', 
            b'\x00\x00'
        ] 

        response_to_client = b''.join(response_to_client)
        self.transport_to_client.write(response_to_client)

        if reply != b'\x00':
            self.transport_to_client.close() # triggers connection_lost()
        else:
            self._next_state()

    def connection_lost(self, exc):
        """Close connection to remote when client connection closed."""

        if exc is not None:
            self.logger.info(str(exc))

        if self.transport_to_remote:
            self.transport_to_remote.close()

    def _tunneling(self, data):
        self.transport_to_remote.write(data)
        
          

