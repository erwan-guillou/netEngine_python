import socket
import cv2
import numpy as np
import struct
import time
import random

MaximumPacketSize = 1400

ip = "127.0.0.1"
broadcast_ip = "127.255.255.255"
port = 8080

messageId = 0
packetId = 0

frame0 = np.zeros((480, 640, 3), dtype=np.uint8)
frame1 = np.zeros((480, 640, 3), dtype=np.uint8)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind((ip,port))

frameCount = 0
while True:
    if frameCount % 30 == 0:
        frame0 = np.full((480, 640, 3), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), dtype=np.uint8)
        frame1 = np.full((480, 640, 3), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), dtype=np.uint8)
    frame = np.vstack((frame0,frame1))
    cv2.imshow("to send", frame)
    _, encoded = cv2.imencode(".jpg",frame)
    data = encoded.tobytes()
    
    bufferToSend = struct.pack("I",len(data)) + data
    dataLength = len(bufferToSend)
    remainingBytes = dataLength
    currentIndex = 0
    packetCount = 0
    while remainingBytes > 0:
        headerSize = 8
        toSend = remainingBytes + headerSize
        if toSend > MaximumPacketSize:
            toSend = MaximumPacketSize - headerSize
        try:
            byteSent = sock.sendto(struct.pack('I',packetCount) +
                                   struct.pack('I',frameCount) +
                                   bufferToSend[currentIndex:currentIndex+toSend-headerSize],
                                   (broadcast_ip,port))
            if byteSent <= 0 or byteSent != toSend:
                raise ValueError("Error on send while sending frame")
        except socket.error:
            raise ValueError("Error on socket while sending frame")
        time.sleep(0.00001)
        currentIndex += byteSent-headerSize
        remainingBytes -= byteSent-headerSize
        packetCount += 1

    ch = chr(cv2.waitKey(int(1000/30)) & 0xFF)
    if ch=='q' or ch=='Q': break
    frameCount += 1

sock.close()