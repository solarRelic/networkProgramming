import socket
import hashlib
import zlib

IP_LOCAL = "127.0.0.1"
IP_TARGET = "127.0.0.1"
TARGET_PORT = 14001
LOCAL_PORT = 15000
LOCAL_ADDR = (IP_LOCAL, LOCAL_PORT)
TARGET_ADDR = (IP_TARGET, TARGET_PORT)

BUFFER_SIZE = 1024
PACKET_CRC_SIZE = 4
PACKET_NUM_SIZE = 4

ACK_SIZE = 4

class Server:

    def __init__ (self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.server.bind(LOCAL_ADDR)
        self.server.settimeout(1)

        self.packetsReceived = {}
        self.hash_received = None
        self.filename_output = ""
        self.amount_of_packets = 0
        self.is_done = False

    def receive_block(self):
        try:
            data, _ = self.server.recvfrom(BUFFER_SIZE)
        except TimeoutError:
            return 
        
        crc_received = int.from_bytes(data[-4:], "big")
        crc_computed = zlib.crc32(data[:-4])
        if crc_received != crc_computed:
            print("[error crc] Received and computed crcs don't add up!")
            return
        
        if (data[:4] == b"DONE"):
            self.is_done = True
            print("End signal is received. Closing.")
            return
        
        self.one_packet(data)

    def one_packet(self, data):
        packet_num_received = int.from_bytes(data[-8:-4], "big")
        if packet_num_received == 0:
            self.hash_received = data[:16]
            self.filename_output = data[16:-8].decode()
            self.send_ack(packet_num_received)
            print("zero packet with info is received.")
        else:
            if packet_num_received in self.packetsReceived:
                self.send_ack(packet_num_received)
                print("packet already exists.")
                return 
            else:
                self.packetsReceived[packet_num_received] = data[:-8]
                self.send_ack(packet_num_received)
                print("packet %d successfully received." %packet_num_received)
                return 
    
    def send_ack(self, packet_num_received):
        ack_packet = bytearray()
        p_n = packet_num_received.to_bytes(ACK_SIZE, "big")
        ack_packet.extend(p_n)
        crc = zlib.crc32(ack_packet)
        c = crc.to_bytes(PACKET_CRC_SIZE, "big")
        ack_packet.extend(c)
        self.server.sendto(ack_packet, TARGET_ADDR)


    def file_from_packets(self):
        packetsReceived = dict(sorted(self.packetsReceived.items()))
        data_out = bytearray()
        for key in packetsReceived.keys():
            data_out.extend(packetsReceived[key])

        hash_computed = hashlib.md5(data_out).digest()
        if self.hash_received == hash_computed:
            with open("save_folder/" + self.filename_output, "wb") as f:
                f.write(data_out)
        else:
            print(self.hash_received)
            print(hash_computed)
            print("[ERROR] Wrong hash!")
            exit(100)


if __name__ == "__main__":
    server = Server()

    while not server.is_done:
        server.receive_block()

    server.file_from_packets()
    print("Success! File received.")
    server.server.close()
