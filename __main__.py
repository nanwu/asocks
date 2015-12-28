
from .client import Client

cli = Client('127.0.01', 1080)
cli.connect(('www.google.com', 80))
cli.sendall(
    b'GET /HTTP/1.1\n'
    b'Host: [rsid].112.2o7.net\n'
    b'Keep-Alive: timeout=15\n'
    b'Connection: Keep-Alive\n'
    b'X-Forwarded-For: 192.168.10.1\n')
print(cli.recvall())
