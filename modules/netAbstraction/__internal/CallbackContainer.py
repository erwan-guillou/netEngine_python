
class CallbackContainer:
    def __init__(self):
        self._cbReceive = []
        self._cbReceiveNextID = 0
        self._cbConnect = []
        self._cbConnectNextID = 0
        self._cbDisconnect = []
        self._cbDisconnectNextID = 0
        self._cbHandshake = []

    def addReceiver(self,callback):
        self._cbReceive.append((self._cbReceiveNextID,callback));
        self._cbReceiveNextID += 1
        return self._cbReceiveNextID - 1
    def removeReceiver(self,id):
        index = -1
        for idx, v in enumerate(self._cbReceive):
            if v[0] == id: index = idx
        if (index >= 0): del self._cbReceive[index]
    def addConnector(self,callback):
        self._cbConnect.append((self._cbConnectNextID,callback));
        self._cbConnectNextID += 1
        return self._cbConnectNextID - 1
    def removeConnector(self,id):
        index = -1
        for idx, v in enumerate(self._cbConnect):
            if v[0] == id: index = idx
        if (index >= 0): del self._cbConnect[index]
    def addDisconnector(self,callback):
        self._cbDisconnect.append((self._cbDisconnectNextID,callback));
        self._cbDisconnectNextID += 1
        return self._cbDisconnectNextID - 1
    def removeDisconnector(self,id):
        index = -1
        for idx, v in enumerate(self._cbDisconnect):
            if v[0] == id: index = idx
        if (index >= 0): del self._cbDisconnect[index]
    def setHandshake(self,callback):
        self._cbHandshake = callback
