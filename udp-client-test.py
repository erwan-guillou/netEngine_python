import sys
import traceback
from os.path import dirname, join

sys.path.append(join(dirname(__file__),"modules"))

for line in sys.path: print(line)

from netAbstraction import Address, ClientUDP
from mykeyboard import KBHit

class ServerHandler:
    client: ClientUDP = None

    @staticmethod
    def initialize(cli:ClientUDP):
        ServerHandler.client = cli
        ServerHandler.client.addReceiver(ServerHandler.receiveData)
        ServerHandler.client.setHandshake(ServerHandler.handshake)

    def receiveData(buffer:bytearray,sender:Address):
        str = buffer.decode('ascii')
        print("> " + str)

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
    loremIpsum = \
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. ", \
        "Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero sit amet quam egestas semper. Aenean ultricies mi vitae est. ", \
        "Mauris placerat eleifend leo. Quisque sit amet est et sapien ullamcorper pharetra. Vestibulum erat wisi, condimentum sed, commodo vitae, ornare sit amet, wisi. Aenean fermentum, elit eget tincidunt condimentum, eros ipsum rutrum orci, sagittis tempor lacus enim ac dui. Donec non enim in turpis pulvinar facilisis. Ut felis. Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue, eu vulputate magna eros eu erat. Aliquam erat volutpat. Nam dui mi, tincidunt quis, accumsan porttitor, facilisis luctus, metus. "

    print("==============================================================================")
    print("== udp-client-test                                NetEngine::NetAbstraction ==")
    print("==============================================================================\n")

    ip = SelectIp()
    port = SelectPort()

    client = ClientUDP(ip,port)
    client._hasUnicast = True
    client._listenUnicast = True
    client._hasBroadcast = True
    client._listenBroadcast = True
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
            if ch=='s' or ch=='S':
                print("Sending lorem ipsum...")
                buffer = bytearray();
                message = input("what message to send: ")
                buffer.extend(map(ord,message))
                client.send(buffer)
        client.stop()
        print("client stopped")
        client.disconnect()
        print("client disconnected")
    except Exception as e:
        print("There was an error", file=sys.stderr)
        print("  Exception: ", e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

main()

