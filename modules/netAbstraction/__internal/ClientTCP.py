import threading
import time
import sys

from .Layers import Address
from .LayerTCP import LayerTCP
from .Client import Client

class ClientTCP(Client):
    def __init__(self,ip = "", port = -1):
        Client.__init__(self,ip,port)
    
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
        self.sock = LayerTCP.connectTo(self.serverAddr)
        if self.sock is None:
            return False
        self.isConnected.set()
        isGood = True
        if self._cbHandshake is not None:
            isGood = self._cbHandshake()
        if isGood:
            for idx, cb in enumerate(self._cbConnect):
                cb[1]()
        else:
            LayerTCP.closeSocket(self.sock)
            self.isConnected.clear()
            return False
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        for idx, cb in enumerate(self._cbDisconnect):
            cb[1]()
        LayerTCP.closeSocket(self.sock)
        self.isConnected.clear()

    def send(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        if LayerTCP.send(self.sock,data,self.serverAddr): return True
        self.disconnect()
        return False
    
    def receive(self,data:bytearray) -> bool:
        if not self.isConnected.is_set(): return False
        client = Address("",-1)
        if LayerTCP.receive(self.sock,data): return True
        self.disconnect()
        return False
    
    def _listenForMessages(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            isGood = True
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            result, readSet = LayerTCP.select(self.sock)
            if not self.isConnected.is_set(): continue
            if self.stopFlag.is_set(): break
            if result < 0:
                print("Error in select")
                isGood = False
            if result > 0 and readSet:
                buffer = bytearray()
                res = LayerTCP.partial_receive(self.sock, buffer)
                if res:
                    if len(buffer) > 0:
                        for idx, cb in enumerate(self._cbReceive):
                            cb[1](buffer)
                else:
                    print("Receive error", file=sys.stderr)
                    isGood = False
        with self.threadsCompletedLock: self.threadsCompleted -= 1
