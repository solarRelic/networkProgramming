import socket
import hashlib
import zlib

IP_LOCAL = "127.0.0.1"
# IP_TARGET = "127.0.0.1"
IP_TARGET = "127.0.0.1"
TARGET_PORT = 14000
LOCAL_PORT = 15001

SERVER_ADDR = (IP_TARGET, TARGET_PORT)

BUFFER_SIZE = 1024
PACKET_CRC_SIZE = 4
PACKET_NUM_SIZE = 4

ACK_SIZE = 4

def md5(filename):
    result = hashlib.md5()
    with open(filename, "rb") as f:
        data_for_hash = f.read()
        result.update(data_for_hash)
    return result.digest()

def main ():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    client.bind(("127.0.0.1", LOCAL_PORT))
    client.settimeout(0.1)

    # dividing a whole file into packets, each one consisting of three parts: 
    # [data | packet_num | crc]
    packets = {}
    filename = input("Enter the file name:\n") 
    file = open(filename, "rb")
    packet_num = 1
    data = file.read(BUFFER_SIZE - (PACKET_CRC_SIZE + PACKET_NUM_SIZE))
    while (data):
        packets[packet_num] = packet_builder(packet_num, data)
        data = file.read(BUFFER_SIZE - (PACKET_CRC_SIZE + PACKET_NUM_SIZE))
        packet_num += 1
    file.close() 
    packets_amount = packet_num - 1

    # sending the name of the file and the amount of packets
    while True:
        name_of_file = packet_amount_and_filename_builder(0, packets_amount, filename)
        client.sendto(name_of_file, SERVER_ADDR)
        try:
            response_from_server, _ = client.recvfrom(ACK_SIZE)
            print("GOT THE ACK FOR THE FILENAME")
        except TimeoutError:
            print("[ACK(filename)] Timeout, didn't receive ACK from the server.")
            continue
        
        ack = int.from_bytes(response_from_server, "big")
        if ack != 0:
            print(ack)
            print("[ACK(filename)(2)] Error. Wrong acknoledgment from the server.")
            continue
        break
    print("[SEND] File's name was sent.")

    for i in packets.keys():
        while True:
            packet_to_send = packets[i]
            client.sendto(packet_to_send, SERVER_ADDR)
            print("packet sent %d/%d" %(i, packets_amount))

            try:
                response_from_server, _ = client.recvfrom(ACK_SIZE)
            except TimeoutError:
                print("[ACK(packet)] Timeout, didn't receive ACK from the server.")
                continue
           
            curr_packet = int.from_bytes(response_from_server, "big")
            if curr_packet != i:
                print("[ACK(packet)(2)] Error. Wrong number of packet.")
                continue
            break

    while True:
        EndOF = ""
        very_last = bytearray()
        very_last.extend(EndOF.encode())
        very_last_crc = zlib.crc32(very_last)
        very_last.extend(very_last_crc.to_bytes(4, "big"))    
        client.sendto(EndOF.encode(), SERVER_ADDR)
        break


def packet_amount_and_filename_builder(packet_num, packets_amount, filename):
    packet = bytearray()
    packet.extend(md5(filename))                               # first 16 bytes are hash
    packet.extend(filename.encode())                           # [filename] after 16 bytes of hash
    packet.extend(packets_amount.to_bytes(4, "big"))           # [packets_am] 
    packet.extend(packet_num.to_bytes(PACKET_NUM_SIZE, "big")) # [packet_num] part of the packet, -8:-4 bytes
    packet_crc = zlib.crc32(packet)
    packet.extend(packet_crc.to_bytes(PACKET_CRC_SIZE, "big")) # [crc] part of the packet, last 4 bytes
    return packet

def packet_builder(packet_num, data):
    packet = bytearray()
    packet.extend(data)                                        # [data] part of the packet
    packet.extend(packet_num.to_bytes(PACKET_NUM_SIZE, 'big')) # [packet_num] part of the packet 
    packet_crc = zlib.crc32(packet)
    packet.extend(packet_crc.to_bytes(PACKET_CRC_SIZE, 'big')) # [crc] part of the packet
    return packet
      

if __name__ == "__main__":
    main()