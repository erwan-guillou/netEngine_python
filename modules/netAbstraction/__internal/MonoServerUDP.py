import threading
import time
import sys

from .interfaces import GetBroadcastAddress
from .Layers import Address
from .LayerUDP import LayerUDP
from .Server import Server

class MonoServerUDP(Server):
    def __init__(self, basePort: int = -1, intf: str = ""):
        Server.__init__(self, basePort, intf)
        self.clients = []
        self.sock = None  # Single socket for both unicast and broadcast
        self._broadcast = Address("", 0)
    
    def start(self) -> bool:
        if self.startedFlag.is_set(): return False
        self.stopFlag.clear()
        thread = threading.Thread(target=self._listenForMessages, daemon=True)
        thread.start()
        self.startedFlag.set()
        return True
    
    def stop(self):
        if not self.startedFlag.is_set(): return
        self.stopFlag.set()
        while True:
            with self.threadsCompletedLock:
                if self.threadsCompleted <= 0: break
            time.sleep(0.1)
        self.startedFlag.clear()
    
    def connect(self) -> bool:
        if self.isConnected.is_set(): return False
        
        # Single socket used for both broadcast and unicast
        self.sock = LayerUDP.openBroadcastSocket(self._port, self.intfToUse)
        if self.sock is None:
            print("Failed to open socket")
            return False
        
        self._broadcast.ip = GetBroadcastAddress(self.intfToUse)
        self._broadcast.port = self._port + 10
        
        self.isConnected.set()
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        LayerUDP.closeSocket(self.sock)
        self.isConnected.clear()
    
    def send(self, data: bytearray) -> None:
        print("bcast [",len(data),",",data,"]")
        LayerUDP.send(self.sock, data, self._broadcast)
    
    def sendTo(self, client: Address, data: bytearray) -> None:
        LayerUDP.send(self.sock, data, client)
    
    def receive(self, client: Address, data: bytearray) -> None:
        pass
    
    def _listenForMessages(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            activity, readfds = LayerUDP.select(self.sock)
            if activity > 0:
                if readfds:
                    buffer = bytearray()
                    recv, addr = LayerUDP.partial_receive(self.sock, buffer)
                    if recv and len(buffer) > 0:
                        knownClient = any(caddr.toString() == addr.toString() for caddr in self.clients)
                        if not knownClient:
                            if self._cbHandshake is not None:
                                if self._cbHandshake(addr, buffer):
                                    self.clients.append(addr)
                                    for cb in self._cbConnect:
                                        cb[1](addr)
                            else:
                                self.clients.append(addr)
                                for cb in self._cbConnect:
                                    cb[1](addr)
                        else:
                            for cb in self._cbReceive:
                                cb[1](addr, buffer)
        with self.threadsCompletedLock: self.threadsCompleted -= 1
