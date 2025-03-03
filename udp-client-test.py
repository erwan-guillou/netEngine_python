import sys
import traceback
from os.path import dirname, join

sys.path.append(join(dirname(__file__),"modules"))

for line in sys.path: print(line)

from netAbstraction import Address, ClientUDP
from mykeyboard import KBHit

import cv2
import numpy as np

class ServerHandler:
    client = None

    @staticmethod
    def initialize(cli):
        ServerHandler.client = cli
        ServerHandler.client.addReceiver(ServerHandler.receiveData)
        ServerHandler.client.setHandshake(ServerHandler.handshake)

    def receiveData(buffer:bytearray,sender:Address):
        print("received frame")
        img = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), 1)
        if img is not None:
            cv2.imshow('frame', img)
            cv2.waitkey(1)

    def handshake() -> bool:
        toSend = bytearray()
        toReceive = bytearray()
        print("handshaking with server")
        name = input("what name to use: ")
        toSend.extend(map(ord,name))
        ServerHandler.client.send(toSend)
        ServerHandler.client.receive(toReceive)
        uuid = toReceive.decode("ascii")
        print("Client uuid is : ", uuid)
        return True

def SelectIp() -> str:
    return input("Enter server Ip : ")

def SelectPort() -> int:
    val = input("Which port to use : ")
    return int(val)

def main():
    print("==============================================================================")
    print("== udp-client-test                                NetEngine::NetAbstraction ==")
    print("==============================================================================\n")

    ip = SelectIp()
    port = SelectPort()

    client = ClientUDP(ip,port)
    ServerHandler.initialize(client)

    try:
        kb = KBHit()
        res = client.connect()
        print("client connected: ", res)
        res = client.start()
        print("client started: ", res)
        while True:
            ch = ''
            if kb.kbhit(): ch = kb.getch()
            if ch=='q' or ch=='Q': break
        client.stop()
        print("client stopped")
        client.disconnect()
        print("client disconnected")
    except Exception as e:
        print("There was an error", file=sys.stderr)
        print("  Exception: ", e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

main()

