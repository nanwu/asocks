import auth
import networking
import functools

from exceptions import InvalidRequest, WrongProtocol, ConnectToRemoteError
from config import *

import asyncio


class Socks5ProtocolState:
    
    INIT = 0
    NEGOTIATED = 1
    AUTHORIZED = 2
    CONNECTED = 3
   
class ServerRemoteProtocol(asyncio.Protocol):
    
    def __init__(self, protocol_to_client):
        self.transport_to_remote = None
        self.transport_to_client = transport_to_client

    def connection_made(self, transport):
        self.transport_to_remote = transport

    def data_received(self, data):
        self.transport_to_client.write(data)  

class ServerClientProtocol(asyncio.Protocol)
    
    def __init__(self):
        self.transport_to_client = None
        self.transport_to_remote = None
        self.state = Socks5Protocol.INIT
        self.remote_host_atype = None

    def _next_state(self, skips=0):
        """ Move protocol state forward by one plus skips"""
        self.state += 1 + skips

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Receive connection from {}.'.format(peername))
        self.transport_to_client = transport
        self._loop = self.transport_to_client._loop

    def data_received(self, data):
        if self.state == Socks5ProtocolState.INIT:
            self._negotiate_auth_method(data)
        elif self.state == Socks5ProtocolState.NEGOTIATED:
            raise NotImplemented 
        elif self.state == Socks5ProtocolState.AUTHORIZED:
            self._accept_connect(data)  
        elif self.state == Socks5ProtocolState.CONNECTED:
            self._tunneling(data)
            

    def _negotiate_auth_method(self, data):
        if len(data) <= 2:
            raise InvalidRequest
        if data[0] != b'\x05':
            raise WrongProtocol

        auth_method_count = int(data[1], 16)
        auth_method_codes = list(data[2:])
        if len(auth_method_codes) < auth_method_count:
            raise InvalidRequest

        # no auth emthod proposed by client is accept
        accepted_code = b'\xff' 

        for auth_method_code in auth_method_codes:
            if auth_method_code in auth.acceptable_auth_method_codes:
                accepted_code = auth_method_code 
                break
        
        respone = b'\x05' + accepted_code
        self.transport_to_client.write(response)
        #self.state = self.state
        
        # skip the auth phase when not required
        self._next_state(self.accepted_code == auth.NoAuthRequired.code)

    def _accept_connect(self, data):
        version = data[:1] 
        assert version == SOCK_PROTOCOL_VERSION 

        cmd = data[1:2]
        assert int(cmd, 16) == 1

        atype = int(data[3:4], 16)
        assert atype in (1, 3, 4) 
        self.remote_host_atype = atype
        if atype == AddressType.IPv6:
            host = '.'.join([str(int(byte, 16)) for byte in data[4:8]])
            port = data[8:10]
        elif atype == AddressType.DomainName:
            addr_octets_count = int(data[4], 16)
            host = data[5:5+addr_octets_count]
            port = data[5+addr_octets_count:7+addr_octets_count]
        else:
            host = ':'.join([str(int(byte, 16)) for byte in data[4:20]])
            port = data[20:22]

        port = struct.unpack('>H', port)[0]

        waiter = asyncio.Future()
        waiter.add_done_callback(self._remote_connected)
        task = self._loop.create_task(self._connect_to_remote(host, port, waiter)) 
    
    @asyncio.coroutine
    def _connect_to_remote(self, host, port, waiter):
	exception = None
        try:
            transport, protocol = yield from asyncio.create_connection(
                functools.partial(ServerRemoteProtocol, 
                                  transport_to_client=self.transport_to_client),
                host, 
                port,
                local_addr=(localhost, port_connect_to_remote))
	except socket.timeout:
	    reply = TTL_EXPIRED
            waiter.set_exception(ConnectToRemoteError(reply))
	except socket.error as err:
	    if err.errno == ENETUNREACH:
		reply = NETWORK_UNREACHABLE
	    elif err.errno == EHOSTUNREACH:
		reply = HOST_UNREACHABLE
	    elif err.errno == ECONNREFUSED:
		reply = CONN_REFUSED
	    else:
		reply = GENERAL_FAIL
            waiter.set_exception(ConnectToRemoteError(reply))
	except:
	    reply = GENERAL_FAIL
            waiter.set_exception(ConnectToRemoteError(reply))
	else:
	    waiter.set_result((transport, protocol))

    def _remote_connected(self, future):
        try:
            self.transport_to_remote = future.result()[0]
        except ConnectToRemoteError as exc:
            reply = struct.pack('>B', self.exc.args[0])
        else:
            reply = b'\x00'   
        
        response_to_client = [
            b'\x05', # protocol version
            reply,   
            b'\x00',  
            struct.pack('>B', self.remote_host_atype),
            b'\x00', 
            b'\x00'
        ] 
        response_to_client = ''.join(response_to_client)
        self.transport_to_client.write(response_to_client)
        if reply != b'\x00':
            self.transport_to_client.close() # triggers connection_lost()

    def connection_lost(self):
        """Need to clean up connection with remote host here"""
        print('Closing connection')
        self.transport_to_remote.close()

    def _tunneling(self, data):
        self.transport_to_remote.write(data)
        
          
loop = asyncio.get_event_loop()
coro = loop.create_server(Socks5Protocol, '127.0.0.1', 1080)
server = loop.run_until_complete(coro)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()

