import socket
import hashlib
import sys
import zlib

IP_LOCAL = "127.0.0.1"
IP_TARGET = "127.0.0.1"
TARGET_PORT = 14000
LOCAL_PORT = 15001

SERVER_ADDR = (IP_TARGET, TARGET_PORT)

BUFFER_SIZE = 1024
PACKET_CRC_SIZE = 4
PACKET_NUM_SIZE = 4

PACKET_ACK_SIZE = 8

PACKET_INFO = 0

class Client:

    def __init__(self, filename):
        self.filename = filename

        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.client.bind((IP_LOCAL, LOCAL_PORT))
        self.client.settimeout(1)

        self.packets = {}
        self.packets_amount = 0
        self.block_size = 10
        self.is_done = False

    # dividing a whole file into packets, each one consisting of three parts: 
    # [data | packet_num | crc]
    def file_into_packets(self):
        file = open(self.filename, "rb")
        packet_num = 1
        data = file.read(BUFFER_SIZE - (PACKET_CRC_SIZE + PACKET_NUM_SIZE))
        while (data):
            self.packets[packet_num] = self.packet_builder(packet_num, data)
            data = file.read(BUFFER_SIZE - (PACKET_CRC_SIZE + PACKET_NUM_SIZE))
            packet_num += 1
        file.close() 
        self.packets_amount = packet_num - 1
        self.packets[0] = self.info_packet_builder(PACKET_INFO)
        self.packets = dict(sorted(self.packets.items()))
        print("construciton successful.")

    def send_block_and_receive_acks(self):
        # sending a block of packets
        amount_of_sent = 0
        for packet_number in self.packets.keys():   
            if amount_of_sent == self.block_size:
                break
            if packet_number in self.packets:
                self.client.sendto(self.packets[packet_number], SERVER_ADDR)
                print("packet %d sent" %packet_number)
                amount_of_sent += 1
                print("amount of sent: %d" %amount_of_sent)

        if (amount_of_sent == 0):
            self.is_done = True

        # receiving the acks for the packets
        for i in range(self.block_size):
            try:
                response, _ = self.client.recvfrom(PACKET_ACK_SIZE)
            except TimeoutError:
                print("[error] didn't receive the ack")   
                return
            
            received_crc = int.from_bytes(response[4:], "big")
            computed_crc = zlib.crc32(response[:4])

            if (received_crc == computed_crc):
                packet_num_delivered = int.from_bytes(response[:4], "big")
                if packet_num_delivered in self.packets:
                    self.packets.pop(packet_num_delivered)
                    print("Packet num. %d successfully delivered (%d)." %(packet_num_delivered, self.packets_amount))
            else:
                print("[error] wrong crc for the ack of a packet")

    def md5(self):
            result = hashlib.md5()
            with open(self.filename, "rb") as f:
                data_for_hash = f.read()
                result.update(data_for_hash)
            return result.digest()
        
    # sends a packet number 0 with the name of the file and a hash
    def info_packet_builder(self, packet_num):
        packet = bytearray()
        packet.extend(self.md5())                                  # first 16 bytes are hash
        packet.extend(self.filename.encode())                      # [filename] after 16 bytes of hash
        packet.extend(packet_num.to_bytes(PACKET_NUM_SIZE, "big")) # [packet_num] part of the packet, -8:-4 bytes
        packet_crc = zlib.crc32(packet)
        packet.extend(packet_crc.to_bytes(PACKET_CRC_SIZE, "big")) # [crc] part of the packet, last 4 bytes
        return packet

    def packet_builder(self, packet_num, data):
        packet = bytearray()
        packet.extend(data)                                        # [data] part of the packet
        packet.extend(packet_num.to_bytes(PACKET_NUM_SIZE, "big")) # [packet_num] part of the packet 
        packet_crc = zlib.crc32(packet)
        packet.extend(packet_crc.to_bytes(PACKET_CRC_SIZE, "big")) # [crc] part of the packet
        return packet
    
    def send_end_signal(self):
        last = bytearray()
        signal = b"DONE"
        last.extend(signal)
        crc = zlib.crc32(last)
        last.extend(crc.to_bytes(PACKET_CRC_SIZE, "big"))
        self.client.sendto(last, SERVER_ADDR)

if __name__ == "__main__":
    client = Client(sys.argv[1])
    client.file_into_packets()

    while not client.is_done:
        client.send_block_and_receive_acks()
    
    print("All packets are sent. Sending the end signal.")
    for i in range(5):
        client.send_end_signal()

    client.client.close()
