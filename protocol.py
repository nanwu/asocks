import auth
from exceptions import InvalidRequest, WrongProtocol

import asyncio

class Socks5ProtocolState:
    
    INIT = 0
    NEGOTIATED = 1
    AUTHORIZED = 2
    CONNECTED = 3
    

class Socks5Protocol(asyncio.Protocol)
    
    def __init__(self):
        self.transport = None
        self.state = Socks5Protocol.INIT

    def _next_state(self, skips=0):
        """ Move protocol state forward by one plus skips"""
        self.state += 1 + skips

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Receive connection from {}.'.format(peername))
        self.transport = transport

    def data_received(self, data):
        if self.state == Socks5ProtocolState.INIT:
            self._negotiate_auth_method(data)
        elif self.state == Socks5ProtocolState.NEGOTIATED:
            raise NotImplemented 
        elif self.state == Socks5ProtocolState.AUTHORIZED:
            self._connect(data)  

         

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
        accepted_code = '\xff' 

        for auth_method_code in auth_method_codes:
            if auth_method_code in auth.acceptable_auth_method_codes:
                accepted_code = auth_method_code 
                break
        
        respone = '\x05' + accepted_code
        self.transport.write(response)
        self.state = self.state
        
        # skip the auth phase when not required
        self._next_state(self.accepted_code == auth.NoAuthRequired.method_code)

    def _connect(self, data):
        version = data[:1] 
        assert version == '\x05'
        cmd = data[1:2]
        assert int(cmd, 16) == 1
        addr_type = int(data[3:4], 16)
        assert addr_type in (1, 3, 4) 
        if addr_type == 1:
            addr = data[4:8]
            addr = ':'.join([for byte in addr])
        elif addr_type == 3:
            addr_octets_count = int(data[4], 16)
            addr = data[5:5+addr_octets_count]
        else:
            addr = data[4:20]


    def _channeling(self, data):
           



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

