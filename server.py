import socket
from errno import ENETUNREACH, EHOSTUNREACH, ECONNREFUSED
import struct
import asyncio 
import logging

STATUS_INIT = 0
STATUS_NEGO_COMPLETE = 1
STATUS_TUNNEL_UP = 2

SUCCEEDED = b'\x00'
GENERAL_FAIL = b'\x01'
NETWORK_UNREACH = b'\x03'
HOST_UNREACH = b'\x04'
CONN_REFUSED = b'\x05'
TTL_EXPIRED = b'\x06'
COMM_NOT_SUPP = b'\x07'
ADDR_TYP_NOT_SUPP = b'\x08'

class AsocksServer:
    
    def __init__(self):
        self._client_status = {}
        self.logger = logging.getLogger('Server')
        self.logger.setLevel(logging.DEBUG)

    def _accept_client(self, reader, writer):
        task = asyncio.Task(self._handle_client(reader, writer))
        #self.clients[task] = (client_reader, client_writer)
        def client_done(task):
            print("client done!")
            del self._client_status[task]

        task.add_done_callback(client_done)
    
    @asyncio.coroutine
    def _handle_client(self, reader, writer):
        status = self._client_status
        status[reader] = STATUS_INIT

        while True:
            try:
                if status[reader] == STATUS_INIT:
                    self._nego(reader, writer)
                elif status[reader] == STATUS_NEGO_COMPLETE:
                    self._handle_request(reader, writer)
            except:
                break

    def _handle_request(self, reader, writer):
        data = yield from reader.read(2)
        assert data[:1] == b'\x05'
        cmd = data[1:2]
        if cmd == b'\x01': # CONNECT
            data = yield from reader.read(2)
            assert data[:1] == b'\x00'
            atyp = data[1:2]
            if atyp == b'\x01' or atyp == b'\x03':
                data = yield from reader.read(1)
                host = yield from reader.read(
                    int.from_bytes(data, byteorder='big'))
                data = yield from reader.read(2)
                port = struct.unpack('>H', data)
                try:
                    remote_reader, remote_writer = yield from (
                        asyncio.open_connection(host, port))
                except socket.timeout:
                    reply = TTL_EXPIRED 
                except socket.error as err:
                    if err.errno == ENETUNREACH:
                        reply = NETWORK_UNREACH 
                    elif err.errno == EHOSTUNREACH:
                        reply = HOST_UNREACH
                    elif err.errno == ECONNREFUSED:
                        reply = CONN_REFUSED 
                    else:
                        reply = GENERAL_FAIL
                except:
                    reply = GENERAL_FAIL
                else:
                    reply = SUCCEEDED
            else:
               reply = ADDR_TYP_NOT_SUPP 
        elif cmd == b'\x02':
            pass
        elif cmd == b'\x03':
            pass
        else:
            reply = COMM_NOT_SUPP
    
        writer.write(b'\x05' + reply + b'\x00\x01\x00\x00\x00\x00\x00\x00')
        if reply == SUCCEEDED:
            self._client_status[reader] = STATUS_TUNNEL_UP
            # remote reader and writer
            _tunneling(reader, writer, remote_reader, remote_writer)
            data = yield from reader.read()

    def _tunneling(down_reader, down_writer, up_reader, up_writer):
        while 1: 
            request_header = b''
            while True:
                line = yield from down_reader.readline()
                if not line:
                    break
                request_header += line
            up_writer.write(request_header) 
            yield from up_writer.drain()
            response_header_fields = []
            content_len = -1
            chunked = False
            while True:
                line = up_reader.readline()  
                if not line:
                   break
                f_name, f_value = line.split(b':', 1)
                if f_name.lower() == b'content-length':
                    content_len = int(f_value.strip())
                if f_name.lower() == b'transfer-encoding'\
                and f_value.strip().lower() == b'chunked':
                    chunked = True
                response_header_entries.append(line) 
            if not chunked and content_len >= 0:
                response_body = yield from up_reader.read(content_len)
            elif chunked:
                response_body = b''
                while True:
                    size = yield from up_reader.readline()
                    size = int(size.strip())
                    chunk = yield from up_reader.read(size)
                    response_body += chunk
                    yield from up_reader.read(2)
                    if size == 0:
                        break
            else:
                self.logger.error("Not chunked and content length not found")
                continue
            down_writer.write(response_body)
            yield from down_writer.drain()
             
                    
    def _nego(self, reader, writer):
        data = yield from reader.read(2)
        if data[:1] != b'\x05':
            raise ProtocolError()
        method_num = ord(data[1:2])
        assert method_num == 1, "Only supported method for server now"
        data = yield from reader.read(method_num)             
        assert data[:1] == b'\x00'
        writer.write(b'\x05\x00')        
        yield from  writer.drain()
        status[reader] == STATUS_NEGO_COMPLETE
    
    def start(self, loop):
        self._server = loop.run_until_complete(
            asyncio.start_server(self._accept_client,
                                        '127.0.0.1', 2080,
                                        loop=loop))

if __name__ == "__main__":
    server = AsocksServer()
    loop = asyncio.get_event_loop()
    server.start(loop)
