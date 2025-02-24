import threading
import time
import sys

from .interfaces import GetLocalIpFromServer
from .Layers import Address
from .LayerUDP import LayerUDP
from .Client import Client

class MonoClientUDP(Client):
    def __init__(self, ip="", port=-1):
        Client.__init__(self, ip, port)
        self._listenMessages = False

    def start(self) -> bool:
        if self.startedFlag.is_set():
            return False
        self.stopFlag.clear()

        if self._listenMessages:
            thread = threading.Thread(target=self._listenForMessages, daemon=True)
            thread.start()

        self.startedFlag.set()
        return True

    def stop(self):
        if not self.startedFlag.is_set():
            return
        self.stopFlag.set()
        while True:
            with self.threadsCompletedLock:
                if self.threadsCompleted <= 0:
                    break
            time.sleep(0.1)
        self.startedFlag.clear()

    def connect(self) -> bool:
        if self.isConnected.is_set():
            return False

        #localIp = GetLocalIpFromServer(self.serverAddr.ip)
        #self.sock = LayerUDP.connectTo(Address(localIp, 0))  # Single socket for both unicast and broadcast
        self.sock = LayerUDP.openBroadcastSocket(self.serverAddr.port,"")
        print("server port : ",self.serverAddr.port)
        if self.sock is None:
            print("Socket connection failed")
            return False
        print("server socket : ",self.sock)

        self.isConnected.set()

        if self._cbHandshake is not None:
            if not self._cbHandshake():
                print("Handshake failed")
                LayerUDP.closeSocket(self.sock)
                self.isConnected.clear()
                return False

        for _, cb in self._cbConnect:
            cb()
        return True

    def disconnect(self):
        if not self.isConnected.is_set():
            return
        for _, cb in self._cbDisconnect:
            cb()
        LayerUDP.closeSocket(self.sock)
        self.isConnected.clear()

    def send(self, data: bytearray) -> bool:
        if not self.isConnected.is_set():
            return False

        if LayerUDP.send(self.sock, data, self.serverAddr):
            return True

        self.disconnect()
        return False

    def receive(self, data: bytearray) -> bool:
        if not self.isConnected.is_set():
            return False

        res, addr = LayerUDP.receive(self.sock, data)
        if not res:
            self.disconnect()
            return False

        return True

    def _listenForMessages(self):
        """Handles both unicast and broadcast reception on a single socket."""
        with self.threadsCompletedLock:
            self.threadsCompleted += 1

        while not self.stopFlag.is_set():
            if not self.isConnected.is_set():
                continue
            if self.stopFlag.is_set():
                break

            result, readSet = LayerUDP.select(self.sock)

            if not self.isConnected.is_set():
                continue
            if self.stopFlag.is_set():
                break

            if result < 0:
                print("Error in select")
                continue

            print(f"post select {result}")
            if result > 0 and readSet:
                buffer = bytearray()
                res, addr = LayerUDP.partial_receive(self.sock, buffer)
                if res and len(buffer) > 0:
                    for _, cb in self._cbReceive:
                        cb(buffer, addr)
                else:
                    print("Receive error", file=sys.stderr)

        with self.threadsCompletedLock:
            self.threadsCompleted -= 1
