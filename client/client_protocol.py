import asyncio
import struct

from networking import *
from auth import *
from config import *

class ClientState:
    INIT = 1
    NEGOTIATED = 2 
    AUTHENTICATED = 3
    CONNECTED_TO_REMOTE = 4
    

class ClientServerProtocol(asyncio.protocol):
    pass

class ClientProtocol(asyncio.protocol):
    
    def __init__(self, remote_domain_name, remote_port=80, waiter):
        self.transport = None
        self._loop = None
        self.state = ClientState.INIT
        self.remote_domain_name = remote_domain_name
        self.remote_port = remote_port
        self.waiter = waiter

    def _next_state(self, skip=0):
        self.state += 1 + skip

    def connection_made(self, transport);
        self.transport = transport
        self._loop = self.transport._loop
        auth_method_selection_msg = SOCK_PROTOCOL_VERSION
        auth_method_selection_msg += struct.pack(
            '>B', 
            len(acceptable_auth_methods))
        auth_method_selection_msg += ''.join(acceptable_auth_method_codes)
        print auth_method_selection_msg
        self.transport.write(auth_method_selection_msg)

    def data_received(self, data):
        if self.state == ClientState.INIT:
            self._process_selected_auth_method(data) 
        elif self.state == ClientState.AUTHENTICATED:
            self._process_connect_reply(data)
        elif self.state == 
        
    def _process_selected_auth_method(self, data):
        assert len(data) == 2
        assert data[0] == SOCK_PROTOCOL_VERSION 
        assert data[1] == NoAuthRequired.code
        if data[1] == NoAuthRequired.code:
            self._next_state(1)
            self._send_connect_request() 

    def _send_connect_request(self):
        connect_msg = SOCK_PROTOCOL_VERSION
        connect_msg += b'\x01'   
        connect_msg += b'\x00'
        connect_msg += struct.pack('>B', AddressType.DomainName)
        connect_msg += self.remote_domain_name.encode('idna') 
        connect_msg += struct.pack('>B', self.remote_port)
        self.transport.write(connect_msg)
        self._next_state()

    def _process_connect_reply(self, data):
        assert data[0] == SOCK_PROTOCOL_VERSION
        connect_status = struct.unpack('>B', data[1:2])
        if connect_status == SUCCEEDED:
            self.waiter.set_result(None)
        else:


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    waiter = loop.create_future()
    watier.add_done_callback()
    conn_coro = create_connection(
        functools.partial(
            ClientProtocol, 
            remote_domain_name='www.bloomberg.com', 
            remote_port=8080, 
            waiter=waiter ), 
        localhost, 
        socks5_server_port, 
        local_addr=(localhost, 8080))
