import threading
import time
import sys

from .interfaces import GetLocalIpFromServer
from .Layers import Address
from .LayerUDP import LayerUDP
from .Client import Client

class ClientBroadcastUDP(Client):
    def __init__(self,ip = "", port = -1):
        Client.__init__(self,ip,port)
        self._unicastSock = None
        self._hasUnicast = False
        self._listenUnicast = False
        self._hasBroadcast = False
        self._listenBroadcast = False
    
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

        self.sock = LayerUDP.openBroadcastSocket(self.serverAddr.port,"")
        if self.sock is None:
            print("no broadcast")
            return False
        
        for idx, cb in enumerate(self._cbConnect):
            cb[1]()
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        for idx, cb in enumerate(self._cbDisconnect):
            cb[1]()
        LayerUDP.closeSocket(self.sock)
        self.isConnected.clear()

    def send(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        return False
    
    def receive(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        return True
    
    def _listenForMessages(self):
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
