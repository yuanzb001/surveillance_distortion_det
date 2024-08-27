import socket
import sys
import threading
import time
from network_util import parse_rtp_packet

def RTP_start(RTP_port):
    monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        monitor_socket.bind(('0.0.0.0', RTP_port))
    except socket.error as msg:
        print(f'Bind failed. Error Code : {str(msg[0])} Message {msg[1]}')
        sys.exit()
    print(f'Socket bind complete. Listening on port {RTP_port}')
    packet_count = 0
    while True:          
        # print('Total ', packet_count, ' package received!')
    # for i in range(100):
        # 接收数据
        data, addr = monitor_socket.recvfrom(4096)  # 缓冲区大小设置为4096字节
        if data != None:
            packet_count += 1
            time.sleep(0.01)

class RTP_receiver:
    def __init__(self, RTP_port):
        self.RTP_port = RTP_port
        self.monitor_socket = None
        self.socket_init()   

    def socket_init(self):
        self.monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.monitor_socket.bind(('0.0.0.0', self.RTP_port))
        except socket.error as msg:
            print(f'Bind failed. Error Code : {str(msg[0])} Message {msg[1]}')
            sys.exit()
        print(f'Socket bind complete. Listening on port {self.RTP_port}')

    def receive_start(self):
        nalu = bytearray()
        packet_count = 0
        nalu_count = 0
        while True:          
            data, addr = self.monitor_socket.recvfrom(4096)  # 缓冲区大小设置为4096字节
            if data != None:
                packet_count += 1
                # print(packet_count)
                time.sleep(0.01)
               
    def close_socket(self):
        if self.monitor_socket != None:
            self.monitor_socket.close()