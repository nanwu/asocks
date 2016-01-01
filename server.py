import socket

STATUS_INIT = 0

class AsocksServer:
	
	def __init__(self):
        self._client_status = {}

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
                    self._stage_nego(reader, writer)
                elif status[reader] == STATUS_NEGO_COMPLETE:
                   except:
                break

    def _stage_handle_request(self, reader, writer):
        data = yield from reader.read(2)
        assert data[:1] == b'\x05'
        cmd = data[1:2]
        if cmd == b'\x01': # CONNECT
            data = yield from reader.read(2)
            assert data[:1] == b'\x00'
            atyp = data[1:2]
            if atyp == b'\x01':
                 
            elif atyp == b'\x03':
                data = yield from reader.read(1)
                data = yield from reader.read(
                    int.from_bytes(data, byteorder='big'))
                
                
            else: # command not supported
                
        
    def _stage_nego(self, reader, writer):
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
            asyncio.start_servr(self._accept_client,
                                        '127.0.0.1', 2080,
                                        loop=loop))

