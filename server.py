import socket
from errno import ENETUNREACH, EHOSTUNREACH, ECONNREFUSED
import struct
import asyncio 
import logging

#from .exceptions import ProtocolError

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
    """
    def _accept_client(self, reader, writer):
        #task = asyncio.Task(self._handle_client(reader, writer))
        #self._client_status[task] = (client_reader, client_writer)

        #def client_done(task):
        #    print("client done!")
        #    del self._client_status[task]

        #task.add_done_callback(client_done)
    """




    @asyncio.coroutine
    def _handle_client(self, reader, writer):
        status = self._client_status
        status[reader] = STATUS_INIT

        while True:
            try:
                if status[reader] == STATUS_INIT:
                    yield from self._nego(reader, writer)
                    status[reader] = STATUS_NEGO_COMPLETE
                elif status[reader] == STATUS_NEGO_COMPLETE:
                    yield from self._handle_request(reader, writer)
            except:
                break
    
    @asyncio.coroutine
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
                port = struct.unpack('>H', data)[0]
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
            yield from self._tunneling(reader, writer, remote_reader, remote_writer)
            data = yield from reader.read()

    @asyncio.coroutine
    def _tunneling(self, down_reader, down_writer, up_reader, up_writer):
        while 1: 
            request_header = b''
            while True:
                line = yield from down_reader.readline()
                request_header += line
                if line == b'\n':
                    break

            up_writer.write(request_header) 
            yield from up_writer.drain()
            content_len = -1
            chunked = False
            status_line = yield from up_reader.readline()
            response_headers = b''
            while True:
                line = yield from up_reader.readline()  
                if line == b'\r\n':
                   break
                f_name, f_value = line.split(b':', 1)
                if f_name.lower() == b'content-length':
                    content_len = int(f_value.strip())
                if f_name.lower() == b'transfer-encoding'\
                and f_value.strip().lower() == b'chunked':
                    chunked = True
                response_headers += line
 
            if not chunked and content_len >= 0:
                response_body = yield from up_reader.read(content_len)
            elif chunked:
                response_body = b''
                import pdb; pdb.set_trace()
                while True:
                    size = yield from up_reader.readline()
                    size = int(size.strip(), 16)
                    if size:
                        chunk = yield from up_reader.readexactly(size)
                        response_body += chunk
                    crlf = yield from up_reader.read(2)
                    if size == 0:
                        break
            else:
                self.logger.error("Not chunked and content length not found")
                continue
            
            import pdb; pdb.set_trace()
            http_response = status_line + response_headers +\
                            b'\r\n' + response_body
            down_writer.write(struct.pack('>I', len(http_response)))
            down_writer.write(http_response)
            yield from down_writer.drain()
    
    @asyncio.coroutine     
    def _nego(self, reader, writer):
        data = yield from reader.read(2)
        if data[:1] != b'\x05':
            raise ProtocolError()
        method_num = ord(data[1:2])
        assert method_num == 1, "Only supported method for server now"
        data = yield from reader.read(method_num)             
        assert data == b'\x00'
        writer.write(b'\x05\x00')        
        yield from writer.drain()
    
    def start(self, loop):
        self._server = loop.run_until_complete(
            asyncio.start_server(self._handle_client,
                                 '127.0.0.1', 2080,
                                 loop=loop)) 
    def stop(self, loop):
        if self._server is not None:
            self._server.close()
            loop.run_until_complete(self._server.wait_closed())
            self._server = None

if __name__ == "__main__":
    server = AsocksServer()
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server.start(loop)
        
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nQuit..")
    
    server.stop(loop)
    loop.close()
    
