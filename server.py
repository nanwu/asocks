import socket

STATUS_INIT = 0

class Server:
	
	def __init__(self):
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._socket.bind(('', 1080))
		self._socket.listen()
		self._status = STATUS_INIT
