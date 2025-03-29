from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP Type for Echo Request


def checksum(source_string):
    """
    Computes the checksum of a given data.
    """
    sum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count += 2

    if countTo < len(source_string):
        sum += source_string[-1]

    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    answer = ~sum & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    """
    Receives the ping reply and calculates the round-trip time.
    """
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        ready = select.select([mySocket], [], [], timeLeft)
        timeSpent = time.time() - startedSelect

        if not ready[0]:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Extract ICMP header from IP packet
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:  # Valid reply
            return f"Reply from {addr[0]}: time={(timeReceived - struct.unpack('d', recPacket[28:])[0]) * 1000:.2f}ms"

        timeLeft -= timeSpent
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    """
    Sends a single ICMP Echo Request packet.
    """
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate checksum
    myChecksum = checksum(header + data)

    # Correct checksum in header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(myChecksum), ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    """
    Performs a single ping operation.
    """
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF

    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay


def ping(host, timeout=1, count=4):
    """
    Pings a host a given number of times.
    """
    dest = gethostbyname(host)
    print(f"Pinging {dest} using Python:\n")

    for i in range(count):
        print(doOnePing(dest, timeout))
        time.sleep(1)


ping("google.com", count=4)
