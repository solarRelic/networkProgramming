# Network Programming: UDP File Transfer with ARQ Protocols

## Overview
This repository contains implementations of two fundamental Automatic Repeat reQuest (ARQ) protocols—Stop-and-Wait ARQ and Selective Repeat ARQ—used for reliable file transfer over UDP. The goal is to enable robust file transmission while handling packet loss, corruption, and ensuring data integrity.

## Implemented Tasks

### 1. Basic UDP File Transfer
The first part of the project establishes a simple UDP-based file transfer system where one application sends a file from disk to a specified IP and port, while another application receives and stores the file.

#### **Key Features:**
- Uses **UDP** for transmission (TCP is not allowed).
- Supports transmission of **any file type** (not just text files).
- Splits the file into **packets of up to 1024 bytes**.
- Ensures proper detection of the **end of file transfer**.
- Transmission is monitored and analyzed using **Wireshark**.

#### **Data Packet Format:**
```
NAME=file.txt
SIZE=1152
START
DATA{4B offset}{data (up to 1020 bytes)}
DATA{4B offset}{data (up to 1020 bytes)}
...
STOP
```

---

### 2. Stop-and-Wait ARQ with Error Detection
This extends the basic UDP transfer by introducing **error detection and reliability mechanisms** through the Stop-and-Wait ARQ protocol.

#### **Enhancements:**
- Implements **checksum-based error detection**:
  - **File-level integrity**: Hash functions (SHA, MD5, etc.).
  - **Packet-level integrity**: CRC-32.
- Uses the **Stop-and-Wait ARQ** algorithm:
  - The sender transmits **one packet at a time** and waits for acknowledgment (ACK).
  - If an error (detected via CRC) is found, the receiver sends a **negative acknowledgment (NAK)**.
  - Lost packets or acknowledgments trigger a **timeout-based retransmission**.
  - The receiver handles duplicate packets if an ACK is lost.
- Communication reliability is **tested using NetDerper**.


---

### 3. Selective Repeat ARQ
The final enhancement replaces Stop-and-Wait with the **Selective Repeat ARQ** protocol, significantly improving efficiency by allowing multiple in-flight packets.

#### **Enhancements:**
- Implements a **sliding window** (size **N**) for efficient data transmission.
- Allows the sender to keep sending packets **until the window limit is reached**.
- The receiver acknowledges each packet individually.
- If an error is detected, **only the corrupted packet is retransmitted** instead of restarting from the lost packet.
- Demonstrates error handling using **NetDerper** to simulate packet loss and corruption.

---

## Tools Used
- **Wireshark** – For analyzing network communication.
- **NetDerper** – To simulate network errors and evaluate protocol robustness.

## How to Run
1. Compile and run the sender application, specifying the destination IP and port.
2. Start the receiver application on the target machine.
3. Monitor the packet flow using Wireshark.
4. Use NetDerper to test fault tolerance and reliability.

---
