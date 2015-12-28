
from .client import Client

cli = Client('127.0.01', 1080)
cli.connect(('www.google.com', 80))
cli.sendall(
    b'GET / HTTP/1.1\n'
    b'Host: www.google.com\n\n')
print(cli.recvall())
