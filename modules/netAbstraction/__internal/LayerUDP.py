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
        dataLength = len(data)
        remainingBytes = dataLength
        currentIndex = 0
        try:
            byteSent = sock.sendto(struct.pack("I",dataLength),(addr.ip,addr.port))
        except socket.error:
            return False
        while remainingBytes > 0:
            toSend = remainingBytes
            if toSend > MaximumPacketSize(sock): toSend = MaximumPacketSize(sock)
            try:
                byteSent = sock.sendto(data[currentIndex:currentIndex+toSend],(addr.ip,addr.port))
                if byteSent <= 0 or byteSent != toSend:
                    return False
            except socket.error:
                return False
            time.sleep(0.00001)
            currentIndex += toSend
            remainingBytes -= toSend
        return True
    
    @staticmethod
    def receive(sock: socket.socket, data: bytearray) -> tuple[bool,Address]:
        addr = ("",0)
        try:
            # Receive the data length first (assuming it's a 4-byte unsigned int)
            length_data, addr = sock.recvfrom(4)
            if len(length_data) != 4:
                return False, Address(addr[0],addr[1])  # Failed to receive the data length
            transmittedLength = struct.unpack("I", length_data)[0]
            print("LayerTCP::receive : ",transmittedLength, " bytes")
            data.clear()  # Clear existing data in the bytearray
            data.extend(bytearray(transmittedLength))  # Resize bytearray
            receivedBytes = 0
            remainingBytes = transmittedLength
            # Receive the actual data
            while receivedBytes < transmittedLength:
                toReceive = min(MaximumPacketSize(sock), remainingBytes)
                chunk, addr = sock.recvfrom(toReceive)
                if len(chunk) == 0:
                    time.sleep(0.00001)  # Sleep for 10 microseconds before retrying
                    continue
                elif len(chunk) < 0:
                    return False, Address(addr[0],addr[1])  # Socket error
                if len(chunk) != toReceive:
                    print(f"Too many bytes received: {len(chunk)} expected: {toReceive}")
                    return False, Address(addr[0],addr[1])  # Unexpected size mismatch
                data[receivedBytes : receivedBytes + len(chunk)] = chunk
                receivedBytes += len(chunk)
                remainingBytes -= len(chunk)
            print("LayerTCP::received : ",len(chunk), " bytes")
            return True, Address(addr[0],addr[1])  # Success
        except socket.error:
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
            tmpData, addr = sock.recvfrom(MaximumPacketSize(sock), socket.MSG_PEEK)
            realAddr = Address(addr[0],addr[1])

            if realAddr.toString() not in LayerUDP.packetsPerSender[sock]:
                tmpData, addr = sock.recvfrom(4)
                if len(tmpData) != 4: return False, realAddr
                transmittedLength = struct.unpack("I", tmpData)[0]
                realData = bytearray(transmittedLength)
                LayerUDP.packetsPerSender[sock][realAddr.toString()] = realData
                LayerUDP.receivedBytesPerSender[sock][realAddr.toString()] = 0
                LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()] = transmittedLength
                return True, realAddr
            else:
                totalLength = LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()]
                currentIndex = LayerUDP.receivedBytesPerSender[sock][realAddr.toString()]
                chunk, addr = sock.recvfrom(len(tmpData))
                bytesReceived = len(chunk)
                LayerUDP.packetsPerSender[sock][realAddr.toString()][currentIndex:currentIndex+bytesReceived] = chunk
                currentIndex += bytesReceived
                LayerUDP.receivedBytesPerSender[sock][realAddr.toString()] = currentIndex
                if currentIndex < totalLength: return True, realAddr
                if currentIndex > totalLength: return False, realAddr
                data.extend(LayerUDP.packetsPerSender[sock][realAddr.toString()])
                del LayerUDP.packetsPerSender[sock][realAddr.toString()]
                del LayerUDP.receivedBytesPerSender[sock][realAddr.toString()]
                del LayerUDP.transmittedBytesPerSender[sock][realAddr.toString()]
                return True, realAddr
        except socket.error:
            return False, realAddr
    