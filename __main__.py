
from .client import Client

cli = Client('127.0.01', 2080)
cli.connect(('www.qq.com', 80))
cli.sendall(
    b'GET / HTTP/1.1\n'
    b'Host: www.qq.com\n\n')
print(cli.recvall())
