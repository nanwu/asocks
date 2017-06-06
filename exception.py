

class ProtocolError(Exception):
    pass

class ProxyAuthError(Exception):
    pass

class ConnectToRemoteError(Exception):
    pass

class ConnectionError(Exception):
    pass

class RequestNotSucceed(Exception):
    pass

class InvalidRequest(Exception):
    pass

class WrongProtocol(InvalidRequest):
    pass
