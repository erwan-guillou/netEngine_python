import threading
import time
import sys

from .interfaces import GetLocalIpFromServer
from .Layers import Address
from .LayerUDP import LayerUDP
from .Client import Client

class ClientUDP(Client):
    def __init__(self,ip = "", port = -1):
        Client.__init__(self,ip,port)
        self._unicastSock = None
        self._hasUnicast = True
        self._listenUnicast = True
        self._hasBroadcast = True
        self._listenBroadcast = True
    
    def start(self) -> bool:
        if self.startedFlag.is_set(): return False
        self.stopFlag.clear()
        if self._hasBroadcast and self._listenBroadcast:
            thread = threading.Thread(target=self._listenForBroadcast, daemon=True)
            thread.start()
        if self._hasUnicast and self._listenUnicast:
            thread = threading.Thread(target=self._listenForUnicast, daemon=True)
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
        if self._hasUnicast:
            localIp = GetLocalIpFromServer(self.serverAddr.ip)
            self._unicastSock = LayerUDP.connectTo(Address(localIp,0))
            if self._unicastSock is None:
                print("no unicast")
                return False
            self.isConnected.set()
            isGood = True
            if self._cbHandshake is not None:
                isGood = self._cbHandshake()
            if not isGood:
                print("no handshake")
                LayerUDP.closeSocket(self._unicastSock)
                self.isConnected.clear()
                return False
        if self._hasBroadcast:
            self.sock = LayerUDP.openBroadcastSocket(self.serverAddr.port + (10 if self._hasUnicast else 0),"")
            if self.sock is None:
                print("no broadcast")
                if self._hasUnicast: LayerUDP.closeSocket(self._unicastSock)
                return False
        for idx, cb in enumerate(self._cbConnect):
            cb[1]()
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        for idx, cb in enumerate(self._cbDisconnect):
            cb[1]()
        if self._hasBroadcast:
            LayerUDP.closeSocket(self.sock)
        if self._hasUnicast:
            LayerUDP.closeSocket(self._unicastSock)
        self.isConnected.clear()

    def send(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        if not self._hasUnicast: return False
        if LayerUDP.send(self._unicastSock,data,self.serverAddr): return True
        self.disconnect()
        return False
    
    def receive(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        if not self._hasUnicast: return False
        res, client = LayerUDP.receive(self._unicastSock,data)
        if not res:
            self.disconnect()
            return False
        return True
    
    def _listenForBroadcast(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            isGood = True
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            result, readSet = LayerUDP.select(self.sock)
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            if result < 0:
                print("Error in select")
                isGood = False
            if result > 0 and readSet:
                buffer = bytearray()
                res, addr = LayerUDP.partial_receive(self.sock, buffer)
                if res:
                    if len(buffer) > 0:
                        for idx, cb in enumerate(self._cbReceive):
                            cb[1](buffer, addr)
                else:
                    print("Receive error", file=sys.stderr)
                    isGood = False
        with self.threadsCompletedLock: self.threadsCompleted -= 1

    def _listenForUnicast(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            isGood = True
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            result, readSet = LayerUDP.select(self._unicastSock)
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            if result < 0:
                print("Error in select")
                isGood = False
            if result > 0 and readSet:
                buffer = bytearray()
                res, addr = LayerUDP.partial_receive(self._unicastSock, buffer)
                if res:
                    if len(buffer) > 0:
                        for idx, cb in enumerate(self._cbReceive):
                            cb[1](buffer, addr)
                else:
                    print("Receive error", file=sys.stderr)
                    isGood = False
        with self.threadsCompletedLock: self.threadsCompleted -= 1