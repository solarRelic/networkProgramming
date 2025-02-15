import socket
import hashlib
import zlib
import collections

IP_LOCAL = "127.0.0.1"
IP_TARGET = "127.0.0.1"

LOCAL_PORT = 15000
TARGET_PORT = 14001

LOCAL_ADDR = (IP_LOCAL, LOCAL_PORT)
TARGET_ADDR = (IP_TARGET, TARGET_PORT)

BUFFER_SIZE = 1024
PACKET_CRC_SIZE = 4
PACKET_NUM_SIZE = 4

ACK_SIZE = 4

def main ():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    server.bind(LOCAL_ADDR)

    filename_output = ""
    packetsReceived = {}
    amount_of_packets = 0
    hash_received = None

    # receive the number 0 packet with the file info (name, hash, amount of packets)
    while True:
        try:
            data, _ = server.recvfrom(BUFFER_SIZE)
        except TimeoutError: 
            continue

        # check crc
        crc_received = int.from_bytes(data[-4:], "big")
        crc_computed = zlib.crc32(data[:-4])
        if crc_received != crc_computed:
            print("[ERROR] Received and computed crcs don't add up!")
            server.sendto(b"error_crc", TARGET_ADDR)
            continue
        
        # check if it's the packet with the filename in it
        packet_num_received = int.from_bytes(data[-8:-4], "big")
        if packet_num_received != 0:
            print("[ERROR] Received packet is wrong!")
            server.sendto(b"error_wrong_packet", TARGET_ADDR) 
            continue

        hash_received = data[:16]
        amount_of_packets = int.from_bytes(data[-12:-8], "big")
        filename_output = (data[16:-12]).decode()
        # send ACK which is equal to 0
        server.sendto(int.to_bytes(0, ACK_SIZE, "big"), TARGET_ADDR)
        print(TARGET_ADDR)
        print("Ack is sent.")
        break

    # receive the file in packets
    for i in range(amount_of_packets):
        while True:
            try:
                data, _ = server.recvfrom(BUFFER_SIZE)
            except TimeoutError: 
                continue   

            # check crc
            crc_received = int.from_bytes(data[-4:], "big")
            crc_computed = zlib.crc32(data[:-4])
            if crc_received != crc_computed:
                # print("received crc: %d" %(crc_received))
                # print("computed crc: %d" %(crc_computed))
                print("[ERROR] Received and computed crcs don't add up!")
                server.sendto(b"error_crc_packet", TARGET_ADDR)
                continue

            curr_packet = int.from_bytes(data[-8:-4], "big")
            print("packet received %d/%d" %(curr_packet, amount_of_packets))
            #loop
            if len(data[:-4]) == 0:
                break
            server.sendto(int.to_bytes(curr_packet, ACK_SIZE, "big"), TARGET_ADDR)
            
            if curr_packet != i+1:
                print("[ERROR] The packet received is not the one that was sent! Listening again...")
                continue

            packetsReceived[curr_packet] = data[:-8]
            break

    # while True:         
    #     try:
    #         response_from_server, _ = server.recvfrom(ACK_SIZE)
    #     except TimeoutError:
    #         print("[ACK(packet)] Timeout, didn't receive ACK from the server.")
    #         continue
    #     crc_received = int.from_bytes(data[-4:], "big")
    #     crc_computed = zlib.crc32(data[:-4])
    #     if crc_received != crc_computed:
    #         # print("received crc: %d" %(crc_received))
    #         # print("computed crc: %d" %(crc_computed))
    #         print("[ERROR] Received and computed crcs don't add up!")
    #         server.sendto(b"error_crc_packet", TARGET_ADDR)
    #         continue
    #     check = response_from_server[:-4].decode()
    #     if check == "EOF":
    #         server.sendto(int.to_bytes(0, ACK_SIZE, "big"), TARGET_ADDR)
    #         break
    #     break

    # write data to a file
    data_out = bytearray()
    od = collections.OrderedDict(sorted(packetsReceived.items()))
    for key in od.keys():
        data_out.extend(od[key])

    hash_computed = hashlib.md5(data_out).digest()
    if hash_received == hash_computed:
        with open(filename_output, "wb") as f:
            f.write(data_out)
    else:
        print(hash_received)
        print(hash_computed)
        print("[ERROR] Wrong hash!")
        return

if __name__ == "__main__":
    main()