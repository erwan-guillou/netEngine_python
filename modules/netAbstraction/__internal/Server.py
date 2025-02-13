
from typing import Callable

from .Layers import Address
from .CallbackContainer import CallbackContainer
from .NetProcess import NetProcess

class Server(CallbackContainer,NetProcess):
    def __init__(self,basePort:int = -1, intf:str = ""):
        CallbackContainer.__init__(self)
        NetProcess.__init__(self,intf)
        self._port = basePort
    
    def addReceiver(self, callback: Callable[[Address,bytearray], None]):
        return super().addReceiver(callback)
    def addConnector(self, callback: Callable[[Address], None]):
        return super().addConnector(callback)
    def addDisconnector(self, callback: Callable[[Address], None]):
        return super().addDisconnector(callback)
    def setHandshake(self, callback: Callable[[Address,bytearray], bool]):
        return super().setHandshake(callback)
    
    def connect(self) -> bool:
        raise NotImplementedError
    def disconnect(self):
        raise NotImplementedError
    def start(self) -> bool:
        raise NotImplementedError
    def stop(self):
        raise NotImplementedError
    def send(self,data:bytearray) -> None:
        raise NotImplementedError
    def sendTo(self,client:Address,data:bytearray) -> None:
        raise NotImplementedError
    def receive(self,client:Address,data:bytearray) -> None:
        raise NotImplementedError
