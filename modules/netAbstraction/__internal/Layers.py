import socket
import struct
import time
import select

class Address:
    def __init__(self,ip:str,port:int):
        self.ip = ip
        self.port = port
    def toString(self) -> str:
        return self.ip + ":" + str(self.port)

def MaximumPacketSize(socket:socket.socket) -> int:
    return 1500

class Layer:
    @staticmethod
    def select(socks: socket.socket|list[socket.socket]) -> tuple[int,bool|list[bool]]:
        if socks is None: return 0, False
        if isinstance(socks, socket.socket): return Layer.__select_one(socks)
        if isinstance(socks, list): return Layer.__select_multi(socks)
        raise NotImplementedError

    @staticmethod
    def closeSocket(sock:socket.socket):
        sock.close()

    @staticmethod
    def __select_one(sock: socket.socket) -> tuple[int, bool]:
        if sock.fileno() == -1:  # Equivalent to checking for InvalidSocket
            return -1, False
        timeout_sec = 0
        timeout_ms = 0.01  # 10 milliseconds converted to seconds
        read_ready, _, _ = select.select([sock], [], [], timeout_ms)
        readSet = bool(read_ready)  # True if data is ready to be read
        return len(read_ready), readSet
    
    @staticmethod
    def __select_multi(socks: list[socket.socket]) -> tuple[int,list[bool]]:
        timeout_sec = 0
        timeout_ms = 10  # 10 milliseconds
        if not socks:
            return 0, []
        readable, _, _ = select.select(socks, [], [], timeout_ms / 1000)
        read_set = [sock in readable for sock in socks]
        return len(readable), read_set
