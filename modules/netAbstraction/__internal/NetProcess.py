import threading

class NetProcess:
    def __init__(self,intf = ""):
        self.sock = None
        self.clientMutex = None
        self.startedFlag = threading.Event()
        self.isConnected = threading.Event()
        self.stopFlag = threading.Event()
        self.threadsCompleted = 0
        self.threadsCompletedLock = threading.Lock()
        self.intfToUse = intf
