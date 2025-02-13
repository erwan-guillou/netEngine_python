
from typing import Callable

from .Layers import Address
from .CallbackContainer import CallbackContainer
from .NetProcess import NetProcess

class Client(CallbackContainer,NetProcess):
    def __init__(self,ip = "", port = -1):
        CallbackContainer.__init__(self)
        NetProcess.__init__(self)
        self.serverAddr = Address(ip,port)
    
    def addReceiver(self, callback: Callable[[bytearray], None]):
        return super().addReceiver(callback)
    def addConnector(self, callback: Callable[[], None]):
        return super().addConnector(callback)
    def addDisconnector(self, callback: Callable[[], None]):
        return super().addDisconnector(callback)
    def setHandshake(self, callback: Callable[[], bool]):
        return super().setHandshake(callback)
    
    def connect(self) -> bool:
        raise NotImplementedError
    def disconnect(self):
        raise NotImplementedError
    def start(self) -> bool:
        raise NotImplementedError
    def stop(self):
        raise NotImplementedError
    def send(self,data:bytearray) -> bool:
        raise NotImplementedError
    def receive(self,data:bytearray) -> bool:
        raise NotImplementedError
