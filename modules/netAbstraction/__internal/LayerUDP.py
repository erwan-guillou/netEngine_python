import socket
import struct
import time

from .Layers import Address, MaximumPacketSize, Layer
from .interfaces import GetAdapterAddress

class LayerUDP(Layer):
    packetsPerSender = {}
    receivedBytesPerSender = {}
    transmittedBytesPerSender = {}

    @staticmethod
    def openSocket(port:int,intf:str = "") -> socket.socket | None:
        try:
            # Create a UDP socket
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            # Allow reusing the same address
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Enable broadcasting
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind to the specified interface and port
            interface = "0.0.0.0"
            if intf != "": interface = GetAdapterAddress(intf)
            udp_sock.bind((interface if interface else "0.0.0.0", port))

            return udp_sock

        except socket.error as e:
            print(f"Failed to create UDP socket: {e}")
            return None
        '''
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(False)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            ip = ""
            if intf != "": ip = GetAdapterAddress(intf)
            sock.bind((ip,port))
            return sock
        except (socket.error, OSError):
            sock.close()  # Close the socket if connection fails
            return None
        '''

    @staticmethod
    def openUnicastSocket(port:int,intf:str = "") -> socket.socket | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(False)
            ip = ""
            if intf != "": ip = GetAdapterAddress(intf)
            sock.bind((ip,port))
            return sock
        except (socket.error, OSError):
            sock.close()  # Close the socket if connection fails
            return None

    @staticmethod
    def openBroadcastSocket(port:int,intf:str = "") -> socket.socket | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setblocking(False)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            ip = ""
            if intf != "": ip = GetAdapterAddress(intf)
            sock.bind((ip,port))
            return sock
        except (socket.error, OSError):
            sock.close()  # Close the socket if connection fails
            return None

    @staticmethod
    def connectTo(addr:Address) -> socket.socket | None:
        print("LayerUDP::connectTo(",addr.toString(),")")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            print(sock)
            sock.bind((addr.ip,addr.port))
            print("bound")
            return sock
        except (socket.error, OSError) as e:
            print(f"Error occurred: {e}")  # Display the error message
            sock.close()  # Close the socket if connection fails
            return None

    @staticmethod
    def send(sock: socket.socket,data: bytearray,addr: Address) -> bool:
        bufferToSend = struct.pack("I",len(data)) + data
        dataLength = len(bufferToSend)
        remainingBytes = dataLength
        currentIndex = 0
        packetCount = 0
        while remainingBytes > 0:
            toSend = remainingBytes + 4
            if toSend > MaximumPacketSize(sock): toSend = MaximumPacketSize(sock)-4
            try:
                byteSent = sock.sendto(struct.pack('I',packetCount) + bufferToSend[currentIndex:currentIndex+toSend-4],(addr.ip,addr.port))
                if byteSent <= 0 or byteSent != toSend:
                    return False
            except socket.error:
                return False
            time.sleep(0.00001)
            currentIndex += byteSent-4
            remainingBytes -= byteSent-4
            packetCount += 1
        return True
    
    @staticmethod
    def receive(sock: socket.socket, data: bytearray) -> tuple[bool,Address]:
        addr = ("",0)
        try:
            data = bytearray()
            while True:
                # wait for first packet of next message
                data, addr = sock.recvfrom(MaximumPacketSize(sock))
                packetId = struct.unpack("I",data[0:4])[0]
                if packetId == 0: break
            transmittedLength = struct.unpack("I", data[4:8])[0]
            chunk = data[8:]
            receivedBytes = len(chunk)
            data += chunk
            remainingBytes = transmittedLength - receivedBytes
            while receivedBytes < transmittedLength:
                toReceive = min(MaximumPacketSize(sock), remainingBytes+4)
                recvdata, addr = sock.recvfrom(toReceive)
                if len(recvdata) == 0:
                    time.sleep(0.00001)  # Sleep for 10 microseconds before retrying
                    continue
                elif len(recvdata) < 0:
                    data = bytearray()
                    return False, Address(addr[0],addr[1])  # Socket error
                if len(recvdata) != toReceive:
                    print(f"Too many bytes received: {len(recvdata)} expected: {toReceive}")
                    data = bytearray()
                    return False, Address(addr[0],addr[1])  # Unexpected size mismatch
                packetId = struct.unpack('I',recvdata)[0]
                chunk = recvdata[4:]
                data += chunk
                receivedBytes += len(chunk)
                remainingBytes -= len(chunk)
            return True, Address(addr[0],addr[1])  # Success
        except socket.error:
            data = bytearray()
            return False, Address(addr[0],addr[1])  # Handle socket errors

    @staticmethod
    def partial_receive(sock: socket.socket, data: bytearray) -> tuple[bool,Address]:
        addr = ("",0)
        data.clear()

        if sock not in LayerUDP.packetsPerSender:
            LayerUDP.packetsPerSender[sock] = {}
            LayerUDP.receivedBytesPerSender[sock] = {}
            LayerUDP.transmittedBytesPerSender[sock] = {}
        
        try:
            tmpData, addr = sock.recvfrom(MaximumPacketSize(sock))
            realAddr = Address(addr[0],addr[1])
            packetId = struct.unpack("I", tmpData[0:4])[0]
            if packetId == 0:
                transmittedLength = struct.unpack("I", tmpData[4:8])[0]
                realData = tmpData[8:]
                LayerUDP.packetsPerSender[sock][realAddr.toString()] = realData
                LayerUDP.receivedBytesPerSender[sock][realAddr.toString()] = len(realData)
                LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()] = transmittedLength
            else:
                if realAddr.toString() not in LayerUDP.packetsPerSender[sock]:
                    True, realAddr
                totalLength = LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()]
                currentIndex = LayerUDP.receivedBytesPerSender[sock][realAddr.toString()]
                chunk = tmpData[4:]
                bytesReceived = len(chunk)
                LayerUDP.packetsPerSender[sock][realAddr.toString()] += chunk
                currentIndex += bytesReceived
                LayerUDP.receivedBytesPerSender[sock][realAddr.toString()] = currentIndex
            currentIndex = LayerUDP.receivedBytesPerSender[sock][realAddr.toString()]
            totalLength = LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()]
            if currentIndex < totalLength:
                print("not enough data")
                return True, realAddr
            if currentIndex > totalLength:
                print("too many data")
                return False, realAddr
            data.extend(LayerUDP.packetsPerSender[sock][realAddr.toString()])
            del LayerUDP.packetsPerSender[sock][realAddr.toString()]
            del LayerUDP.receivedBytesPerSender[sock][realAddr.toString()]
            del LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()]
            return True, realAddr
        except socket.error:
            print("socket error")
            return False, realAddr
    