import sys
import traceback
from os.path import dirname, join

sys.path.append(join(dirname(__file__),"modules"))

from netAbstraction import GetAdapterList, GetAdapterAddress
from netAbstraction import Address,ServerTCP
from mykeyboard import KBHit

class ClientHandler:
    server: ServerTCP = None
    names: dict = {}

    @staticmethod
    def initialize(srv:ServerTCP):
        ClientHandler.server = srv
        ClientHandler.server.addReceiver(ClientHandler.receivedData)
        ClientHandler.server.addConnector(ClientHandler.connectedClient)
        ClientHandler.server.addDisconnector(ClientHandler.disconnectedClient)
        ClientHandler.server.setHandshake(ClientHandler.handshake)

    def receivedData(cli:Address,buffer:bytearray):
        print("received data")
        str = buffer.decode('ascii')
        toSend = ClientHandler.names[cli.toString()] + " said " + str
        vec = bytearray()
        vec.extend(map(ord,toSend))
        ClientHandler.server.send(vec)
    def connectedClient(cli:Address) -> None:
        toSend = ClientHandler.names[cli.toString()] + " just arrived"
        vec = bytearray()
        vec.extend(map(ord,toSend))
        ClientHandler.server.send(vec)
    def disconnectedClient(cli:Address) -> None:
        toSend = ClientHandler.names[cli.toString()] + " just quit"
        del ClientHandler.names[cli.toString()]
        vec = bytearray()
        vec.extend(map(ord,toSend))
        ClientHandler.server.send(vec)
    def handshake(cli:Address,buffer:bytearray) -> bool:
        toSend = bytearray()
        toReceive = bytearray()
        print("handshaking with client")
        ClientHandler.server.receive(cli,toReceive)
        name = toReceive.decode('ascii')
        toSend = cli.toString().encode('ascii')
        ClientHandler.server.send(toSend)
        ClientHandler.names[cli.toString()] = name
        return True

def SelectAdapter() -> str:
    adapters = GetAdapterList()
    for idx, adapter in enumerate(adapters):
        print(idx, " :: ",adapter, " -> ", GetAdapterAddress(adapter));
    index = int(input("Enter adapter index : "))
    print("--> [",adapters[index],"]")
    return adapters[index]

def SelectPort() -> int:
    val = input("Which port to use : ")
    return int(val)

def main():
    print("==============================================================================")
    print("== tcp-server-test                                NetEngine::NetAbstraction ==")
    print("==============================================================================\n")

    adapter = SelectAdapter()
    port = SelectPort()
    
    server = ServerTCP(port, adapter)
    ClientHandler.initialize(server)

    try:
        kb = KBHit()
        server.connect()
        print("server connected")
        server.start()
        print("server started")
        while True:
            ch = ''
            if kb.kbhit(): ch = kb.getch()
            if ch=='q' or ch=='Q': break
        server.stop()
        print("server stopped")
        server.disconnect()
        print("server disconnected")
    except Exception as e:
        print("There was an error", file=sys.stderr)
        print("  Exception: ", e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

main()
