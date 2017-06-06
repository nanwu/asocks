
SOCK_PROTOCOL_VERSION = 5

class AddressType:
    IPv4 = 1
    IPv6 = 4
    DomainName = 3

class ConnectionStatus:
    SUCCEEDED = 0 
    GENERAL_FAIL = 1 
    NOT_ALLOWED_BY_RULESET = 2
    NETWORK_UNREACHABLE = 3 
    HOST_UNREACHABLE = 4 
    CONN_REFUSED = 5 
    TTL_EXPIRED = 6 
    COMM_NOT_SUPP = 7 
    ATYP_NOT_SUPP = 8 

