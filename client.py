#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import struct
from .exceptions import ProtocolError, ProxyAuthError, RequestNotSucceed

STATUS_INIT = 0
STATUS_NEGO = 1
STATUS_AUTHENTICATED = 2
STATUS_CONN_ESTABLISHED = 3


class ClientState:
    INIT = 1
    NEGOTIATED = 2 
    AUTHENTICATED = 3
    CONNECTED_TO_REMOTE = 4
 
BUFF_SIZE = 1024*1024

class Client:

    def __init__(self, proxy_host, proxy_port, username=None, password=None):
        self._status = STATUS_INIT
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._proxy_addr = proxy_host, proxy_port
        self._username = username
        self._pasword = password
        if username and password:
            self._auth_data_chunk = b'\x05\x02\x00\x02'
        else:
            self._auth_data_chunk = b'\x05\x01\x00'

    def _negotiate(self):
        try:
            self._socket.connect(self._proxy_addr)
            print('connected to server')
        except socket.error as e:
            self._socket.close()
            print("Error connecting to proxy {0}:{1}".format(*self._proxy_addr))
        else:
            try:
                self._socket.send(self._auth_data_chunk)
                print("auth request sent out")
                method_selected = self._socket.recv(2)
            except socket.error as e:
                print("Error send auth data", e)
                pass    
            else:
                if method_selected[0:1] != b'\x05':
                    raise ProtocolError()   
                
                # http://tools.ietf.org/html/rfc1929
                if method_selected[1:2] == b'\x02':
                    self._socket.send(b'\x01' + hex(len(self._username).encode())
                                      + self._username.encode()
                                      + hex(len(self._password).encode())
                                      + self._password.encode())
                    res = self._socket.recv(4)
                    if res[0:1] != b'\x01':
                        raise ProtocolError()

                    if res[1:] != b'\x00':
                        self._socket.close()    
                        raise ProxyAuthError()
                elif method_selected[1:2] != b'\x00':
                    raise ProtocolError()               
                self._status = STATUS_AUTHENTICATED


    def connect(self, dest):
        if self._status == STATUS_INIT:
            self._negotiate()
        
        assert self._status == STATUS_AUTHENTICATED,\
               "need authenticated before connect"
        self._send_conn_request(dest)
        print("connect request sent out")
        try:
            bnd_addr, bnd_port = self._recv_conn_reponse()          
            self._status = STATUS_CONN_ESTABLISHED
        except:
            pass
        
    def sendall(self, _bytes):
        data_length = self._socket.sendall(_bytes)
        
    def recvall(self):
        data = b''
        size = self._recvexactly(4)
        size = struct.unpack('>I', size)[0]
        data = self._recvexactly(size)
        return data

    def _recvexactly(self, size):
        data = b''
        while size:
            res = self._socket.recv(size)
            data += res
            size -= len(res)
        return data

    def _send_conn_request(self, dest):
        host, port = dest
        request_content = b'\x05' + b'\x01' + b'\x00'
        try:
            request_content += b'\x01' + socket.inet_aton(host)
        except socket.error:
            host_bytes = host.encode('idna')
            request_content += b'\x03' + chr(len(host_bytes)).encode() + host_bytes
        request_content += struct.pack('>H', port)
        self._socket.send(request_content)

    def _recv_conn_reponse(self):   
        res = self._socket.recv(255) # to be verified
        # check version
        ver, res = res[:1], res[1:]
        if ver != b'\x05':
            raise ProtocolError()
        # check reply
        rep, res = res[:1], res[1:] 
        if rep != b'\x00':
            raise RequestNotSucceed()
        
        # address type
        addr_type, res = res[1:2], res[2:]
        if addr_type == b'\x01': # ipv4 
            addr, res = res[:4], res[4:]
            addr = socket.inet_ntoa(addr)   
        elif addr_type == b'\x03': # dns
            _len = ord(res[:1])
            addr, res = res[1:1+_len], res[1+_len:] 
        
        port = struct.unpack('>H', res[:2])[0]
        return addr, port
    

class ClientThread(Thread):
    
    def __init__(self)




