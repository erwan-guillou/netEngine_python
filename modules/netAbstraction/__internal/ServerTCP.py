import threading
import time
import sys

from .Layers import Address
from .LayerTCP import LayerTCP
from .Server import Server

class ServerTCP(Server):
    def __init__(self,basePort:int = -1, intf:str = ""):
        Server.__init__(self,basePort,intf)
        self._toSocket = {}
        self._fromSocket = {}
        self._listenTo = []
    
    def start(self) -> bool:
        if self.startedFlag.is_set(): return False
        self.stopFlag.clear()
        thread = threading.Thread(target=self._acceptClients, daemon=True)
        thread.start()
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
        self.sock = LayerTCP.openSocket(self._port, self.intfToUse)
        if self.sock is None:
            return False
        self.isConnected.set()
        return True
    
    def disconnect(self):
        if not self.isConnected.is_set(): return
        LayerTCP.closeSocket(self.sock)
        self.isConnected.clear()

    def send(self,data:bytearray) -> None:
        disconnected = []
        for cli in self._fromSocket.keys():
            if not LayerTCP.send(cli,data,self._fromSocket[cli]):
                disconnected.append(cli)
        for cli in disconnected:
            for idx, cb in enumerate(self._cbDisconnect):
                cb[1](self._fromSocket[cli])
            del self._toSocket[self._fromSocket[cli].toString()]
            del self._fromSocket[cli]
            self._listenTo.remove(cli)
    def sendTo(self,client:Address,data:bytearray) -> None:
        disconnected = []
        if not LayerTCP.send(self._toSocket[client.toString()],data,client):
            disconnected.append(cli)
        for cli in disconnected:
            for idx, cb in enumerate(self._cbDisconnect):
                cb[1](self._fromSocket[cli])
            del self._toSocket[self._fromSocket[cli].toString()]
            del self._fromSocket[cli]
            self._listenTo.remove(cli)
    def receive(self,client:Address,data:bytearray) -> None:
        disconnected = []
        if not LayerTCP.receive(self._toSocket[client.toString()],data):
            disconnected.append(cli)
        for cli in disconnected:
            for idx, cb in enumerate(self._cbDisconnect):
                cb[1](self._fromSocket[cli])
            del self._toSocket[self._fromSocket[cli].toString()]
            del self._fromSocket[cli]
            self._listenTo.remove(cli)
    
    def _acceptClients(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            if not self.isConnected.is_set(): continue
            result, readSet = LayerTCP.select(self.sock)
            if result > 0 and readSet:
                cliSoc, cliAddr = LayerTCP.acceptClient(self.sock)
                self._toSocket[cliAddr.toString()] = cliSoc
                self._fromSocket[cliSoc] = cliAddr
                isGood = True
                if self._cbHandshake:
                    isGood = self._cbHandshake(cliAddr,bytearray())
                if isGood:
                    for idx, cb in enumerate(self._cbConnect):
                        cb[1](cliAddr)
                    self._listenTo.append(cliSoc)
                else:
                    del self._toSocket[cliAddr.toString()]
                    del self._fromSocket[cliSoc]
                    LayerTCP.closeSocket(cliSoc)
        
        with self.threadsCompletedLock: self.threadsCompleted -= 1

    def _listenForMessages(self):
        with self.threadsCompletedLock: self.threadsCompleted += 1
        while not self.stopFlag.is_set():
            _disconnected = []
            _from = []
            _data = []
            selectResult, readSet = LayerTCP.select(self._listenTo)
            if selectResult > 0:
                for index, (hasData, it) in enumerate(zip(readSet,self._listenTo)):
                    if not hasData: continue
                    client = self._fromSocket[it]
                    buffer = bytearray()
                    if not LayerTCP.partial_receive(it,buffer):
                        _disconnected.append(it)
                    elif len(buffer)>0:
                        _from.append(client)
                        _data.append(buffer)
            for cli in _disconnected:
                for idx, cb in enumerate(self._cbDisconnect):
                    cb[1](self._fromSocket[cli])
                del self._toSocket[self._fromSocket[cli].toString()]
                del self._fromSocket[cli]
                self._listenTo.remove(cli)
            for index, (client, buffer) in enumerate(zip(_from,_data)):
                for idx, cb in enumerate(self._cbReceive):
                    cb[1](client,buffer)
        with self.threadsCompletedLock: self.threadsCompleted -= 1
