import socket
import struct
import time

from .Layers import Address, MaximumPacketSize, Layer
from .interfaces import GetAdapterAddress

class LayerTCP(Layer):
    packetsPerSender = {}
    receivedBytesPerSender = {}
    transmittedBytesPerSender = {}

    @staticmethod
    def openSocket(port:int,intf:str="") -> socket.socket | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = GetAdapterAddress(intf)
            sock.bind((ip,port))
            sock.listen(10)
            return sock
        except (socket.error, OSError):
            sock.close()  # Close the socket if connection fails
            return None

    @staticmethod
    def connectTo(addr:Address) -> socket.socket | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((addr.ip,addr.port))  # addr should be (IP, Port) tuple
            return sock
        except (socket.error, OSError):
            sock.close()  # Close the socket if connection fails
            return None
    
    @staticmethod
    def acceptClient(sock:socket.socket):
        res = sock.accept()
        return res[0], Address(res[1][0],res[1][1])
    
    @staticmethod
    def send(sock: socket.socket,data: bytearray,addr: Address) -> bool:
        dataLength = len(data)
        remainingBytes = dataLength
        currentIndex = 0
        try:
            byteSent = sock.send(struct.pack("I",dataLength))
        except socket.error:
            return False
        while remainingBytes > 0:
            toSend = remainingBytes
            if toSend > MaximumPacketSize(sock): toSend = MaximumPacketSize(sock)
            try:
                byteSent = sock.send(data[currentIndex:currentIndex+toSend])
                if byteSent <= 0 or byteSent != toSend:
                    return False
            except socket.error:
                return False
            time.sleep(0.00001)
            currentIndex += toSend
            remainingBytes -= toSend
        return True
    
    @staticmethod
    def receive(sock: socket.socket, data: bytearray) -> bool:
        try:
            # Receive the data length first (assuming it's a 4-byte unsigned int)
            length_data = sock.recv(4)
            if len(length_data) != 4:
                return False  # Failed to receive the data length
            transmittedLength = struct.unpack("I", length_data)[0]
            print("LayerTCP::receive : ",transmittedLength, " bytes")
            data.clear()  # Clear existing data in the bytearray
            data.extend(bytearray(transmittedLength))  # Resize bytearray
            receivedBytes = 0
            remainingBytes = transmittedLength
            # Receive the actual data
            while receivedBytes < transmittedLength:
                toReceive = min(MaximumPacketSize(sock), remainingBytes)
                chunk = sock.recv(toReceive)
                if len(chunk) == 0:
                    time.sleep(0.00001)  # Sleep for 10 microseconds before retrying
                    continue
                elif len(chunk) < 0:
                    return False  # Socket error
                if len(chunk) != toReceive:
                    print(f"Too many bytes received: {len(chunk)} expected: {toReceive}")
                    return False  # Unexpected size mismatch
                data[receivedBytes : receivedBytes + len(chunk)] = chunk
                receivedBytes += len(chunk)
                remainingBytes -= len(chunk)
            print("LayerTCP::received : ",len(chunk), " bytes")
            return True  # Success
        except socket.error:
            return False  # Handle socket errors

    @staticmethod
    def partial_receive(sock: socket.socket, data: bytearray) -> bool:
        data.clear()

        if sock not in LayerTCP.packetsPerSender:
            try:
                length_data = sock.recv(4)
                if len(length_data) == 0:
                    return True  # No data available
                elif len(length_data) < 4:
                    return False  # Error: Partial length received

                length = struct.unpack("I", length_data)[0]
                buffer = bytearray(length)
                LayerTCP.receivedBytesPerSender[sock] = 0
                LayerTCP.transmittedBytesPerSender[sock] = length
                LayerTCP.packetsPerSender[sock] = buffer
                print("LayerTCP::receive : ",length, " bytes")
            except socket.error:
                return False  # Error occurred during receive
        else:
            totalLength = LayerTCP.transmittedBytesPerSender[sock]
            currentIndex = LayerTCP.receivedBytesPerSender[sock]
            remainingBytes = totalLength - currentIndex

            if remainingBytes > MaximumPacketSize(socket):
                remainingBytes = MaximumPacketSize(socket)

            try:
                chunk = sock.recv(remainingBytes)
                bytesReceived = len(chunk)
                LayerTCP.packetsPerSender[sock][currentIndex:currentIndex+bytesReceived] = chunk
                currentIndex += bytesReceived
                LayerTCP.receivedBytesPerSender[sock] = currentIndex
                print("LayerTCP::received : ",len(chunk), " bytes")

                if currentIndex < totalLength:
                    return True  # Still receiving
                if currentIndex > totalLength:
                    return False  # Received too many bytes (error)

                # Transfer complete, copy data and clean up
                data.extend(LayerTCP.packetsPerSender[sock])  # Copy to output
                del LayerTCP.packetsPerSender[sock]
                del LayerTCP.receivedBytesPerSender[sock]
                del LayerTCP.transmittedBytesPerSender[sock]

            except socket.error:
                return False  # Error during receive

        return True
