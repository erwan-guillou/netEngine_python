import threading
import time
import sys

from .interfaces import GetBroadcastAddress
from .Layers import Address
from .LayerUDP import LayerUDP
from .Server import Server

class ServerUDP(Server):
    def __init__(self,basePort:int = -1, intf:str = ""):
        Server.__init__(self,basePort,intf)
        self.clients = []
        self._unicastSock = None
        self._broadcast = Address("",0)
    
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
        
        self.sock = LayerUDP.openBroadcastSocket(self._port + 10,self.intfToUse)
        if self.sock is None:
            print("no broadcast")
            return False
        
        self._unicastSock = LayerUDP.openUnicastSocket(self._port,self.intfToUse)
        if self._unicastSock is None:
            print("no unicast")
            LayerUDP.closeSocket(self.sock)
            return False
        
        self._broadcast.ip = GetBroadcastAddress(self.intfToUse)
        print(self._broadcast.ip)
        self._broadcast.port = self._port+10

        self.isConnected.set()
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        LayerUDP.closeSocket(self._unicastSock)
        LayerUDP.closeSocket(self.sock)
        self.isConnected.clear()

    def send(self,data:bytearray) -> None:
        LayerUDP.send(self.sock,data,self._broadcast)

    def sendTo(self,client:Address,data:bytearray) -> None:
        LayerUDP.send(self._unicastSock,data,client)

    def receive(self,client:Address,data:bytearray) -> None:
        pass
    
    def _listenForMessages(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            activity, readfds = LayerUDP.select(self._unicastSock)
            if activity > 0:
                if readfds:
                    buffer = bytearray()
                    recv, addr = LayerUDP.partial_receive(self._unicastSock,buffer)
                    if recv and len(buffer) > 0:
                        knownClient = False
                        for idx, caddr in enumerate(self.clients):
                            if caddr.toString() == addr.toString(): knownClient = True
                        if not knownClient:
                            if self._cbHandshake is not None:
                                if self._cbHandshake(addr,buffer):
                                    self.clients.append(addr)
                                    for idx, cb in enumerate(self._cbConnect):
                                        cb[1](addr)
                                else:
                                    pass
                            else:
                                self.clients.append(addr)
                                for idx, cb in enumerate(self._cbConnect):
                                    cb[1](addr)
                                for idx, cb in enumerate(self._cbReceive):
                                    cb[1](addr,buffer)
                        else:
                            for idx, cb in enumerate(self._cbReceive):
                                cb[1](addr,buffer)
        with self.threadsCompletedLock: self.threadsCompleted -= 1
