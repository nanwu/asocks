# Asocks

[![PyPI version](https://badge.fury.io/py/asocks.svg)](https://badge.fury.io/py/asocks)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A SOCKS5 proxy client/server built on top of asyncio: the Python3 library which provides infrastructure for writing single-thread concurrent code and other high level networking APIs.

This project currently is in BETA version with proxy server fully functioning. More features will come soon.
## Installation

pip3 install asocks

## Usage
```
  asocks-server 
  asocks-server -p 2081
  asocks-server -p 2081 -c 1024
  asocks-server -p 2081 -c 2014 --local
```

optional arguments:
```
  -h, --help            show this help message and exit
  -p PORT, --port PORT  specify port number proxy listens on. Default to port 2080
  -c CONCURRENCY, --concurrency CONCURRENCY
                        max concurrent connections server will accept. Default to 256
  -l, --local           run server at localhost
```

## Contributing

Patches are welcomed! Please create specific branch for feature or fix.

## License

MIT
