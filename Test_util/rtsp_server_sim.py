import socket
import threading
import struct
import time
import random
import multiprocessing


class rtsp_sender_line():
    def __init__(self):
        self.realm = "Login to AMC060B81B860387E8"
        self.nonce = "586c105ffbf43201496ba72acf7a34d9"
        self.host = '127.0.0.1'
        self.port = 8554
        self.rtp_port = 5004
        self.username = 'admin'
        self.password = 'Bearcat$'
        self.auth_flag = False
        self.streaming = False
        self.setup_rtp_socket()

        self.RTP_VERSION = 2
        self.RTP_PAYLOAD_TYPE = 96
        self.RTP_SEQUENCE_NUMBER = 0
        self.RTP_TIMESTAMP = 0
        self.RTP_SSRC = 0x12345678
        self.package_sent_count = 0
        self.nalu_count = 0
        self.nalu_list = []
        self.video_path = '/home/yuanzn/Documents/NSF_cohort/Demo_code_v1/test_data/1_Too_much_noise.h264'
        self.get_nalu_list()   

    def send_rtp_packet(self, payload, client_socket):
        self.nalu_count += 1
        random_rate = 0
        packet_count = 0
        if self.RTP_SEQUENCE_NUMBER >= 65535:
            self.RTP_SEQUENCE_NUMBER = 0
        if len(payload) <= 1400:
            self.RTP_SEQUENCE_NUMBER += 1
            if self.RTP_SEQUENCE_NUMBER > 65535:
                self.RTP_SEQUENCE_NUMBER = 0
            # print(self.RTP_SEQUENCE_NUMBER)
            self.RTP_TIMESTAMP += 3000  # Simulated frame interval
            rtp_header = struct.pack('!BBHII',
                                 0x80,
                                 self.RTP_PAYLOAD_TYPE,
                                 self.RTP_SEQUENCE_NUMBER,
                                 self.RTP_TIMESTAMP,
                                 self.RTP_SSRC)
            rtp_packet = rtp_header + payload
            # self.rtp_socket.sendto(rtp_packet, client_socket.getpeername())
            print(self.RTP_SEQUENCE_NUMBER)
            self.rtp_socket.sendto(rtp_packet, (self.host, self.rtp_port))
            self.package_sent_count += 1
            print(self.package_sent_count, 'package sent!')
            # time.sleep(0.001)
            # print(len(rtp_packet),' bytes Package sent with ', len(payload), ' bytes payload')
        else:
            target_loss_count = int((len(payload) / 1400) * random_rate)
            packet_counts = int(len(payload) / 1400)
            packet_count = 0
            rand_select = []
            if target_loss_count > 1 and (self.nalu_count > 200 and self.nalu_count < 1100):
                range_sample = range(packet_counts)[1: packet_counts - 2]
                rand_select = random.sample(range_sample, target_loss_count)
                print('random select: ', rand_select)
            nal_header = payload[0]
            fu_indicator = (nal_header & 0xE0) | 28  # FU-A indicator
            fu_header_s = 0x80 | (nal_header & 0x1F)  # Start bit set
            fu_header_e = 0x40 | (nal_header & 0x1F)  # End bit set
            fu_header = 0x1F  # No start, no end

            payload_len = len(payload)
            offset = 1  # Skip the first byte (NAL header)
            start_flag = True
            self.RTP_TIMESTAMP += 3000  # Simulated frame interval
            while offset < payload_len:
                packet_count += 1
                self.RTP_SEQUENCE_NUMBER += 1
                if self.RTP_SEQUENCE_NUMBER > 65535:
                    self.RTP_SEQUENCE_NUMBER = 0
                # print(self.RTP_SEQUENCE_NUMBER)              
                rtp_header = struct.pack('!BBHII',
                                 0x80,
                                 self.RTP_PAYLOAD_TYPE,
                                 self.RTP_SEQUENCE_NUMBER,
                                 self.RTP_TIMESTAMP,
                                 self.RTP_SSRC)
                remaining = payload_len - offset
                if start_flag:
                    fu_header = fu_header_s
                    start_flag = False
                else:
                    if remaining <= 1400:
                        fu_header = fu_header_e
                        marker = 1
                    else:
                        fu_header = 0x1F
                        marker = 0
                rtp_packet = rtp_header + struct.pack('!BB', fu_indicator, fu_header) + payload[offset:offset+1400]
                # self.rtp_socket.sendto(rtp_packet, client_socket.getpeername())
                # print(self.RTP_SEQUENCE_NUMBER)
                # print(packet_count)
                if packet_count not in rand_select:
                    self.rtp_socket.sendto(rtp_packet, (self.host, self.rtp_port))
                else:
                    print('the packet was skipped!')
                # self.rtp_socket.sendto(rtp_packet, (self.host, self.rtp_port))
                self.package_sent_count += 1
                print(self.package_sent_count, 'package sent!')
                # time.sleep(0.001)
                # print(len(rtp_packet),' bytes Package sent with ', len(payload), ' bytes payload')
                # if not (remaining <= 1400):
                #     self.RTP_SEQUENCE_NUMBER += 1
                offset += 1400 
                # rtp_header = struct.pack('!BBHII',
                #                  0x80,
                #                  self.RTP_PAYLOAD_TYPE,
                #                  self.RTP_SEQUENCE_NUMBER,
                #                  self.RTP_TIMESTAMP,
                #                  self.RTP_SSRC)
                fu_header = 0x1F  # Clear start bit
    
    # def send_rtp_packet(self, payload, client_socket):
    #     data = 'rtp test'
    #     print(data)
    #     self.rtp_socket.sendto(data.encode(), (self.host, self.rtp_port))

    def setup_rtp_socket(self):
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.rtp_socket.connect((self.host, self.rtp_port))
    
    def validate_auth(self, auth):
        return True


    def get_nalu_list(self):
        def find_start_code(buffer):
            # for i in range(len(buffer) - 3):
            #     if buffer[i] == 0 and buffer[i + 1] == 0 and buffer[i + 2] == 0 and buffer[i + 3] == 1:
            #         return i, 4
            for i in range(len(buffer) - 2):
                if buffer[i] == 0 and buffer[i + 1] == 0 and buffer[i + 2] == 1:
                    return i, 3
                elif i < len(buffer) - 3 and buffer[i] == 0 and buffer[i + 1] == 0 and buffer[i + 2] == 0 and buffer[i + 3] == 1:
                    return i, 4
            return -1, -1
        with open(self.video_path, 'rb') as f:
            data = f.read() 
            offset = 0
            print('the file size is ', len(data))
            # print('start sending rtp')
            print('opening h264 file')  
            while offset < len(data):
                print('the offset left:', offset)
                previous_time = time.time()
                # start = find_start_code(data[offset:])
                start, start_flag = find_start_code(data[offset:])
                dura_time = time.time() - previous_time
                # print('time for find one nalu start:', dura_time)
                # print(start)
                if start == -1:
                    break
                # end = find_start_code(data[offset + start + 4:])
                end, end_flag = find_start_code(data[offset + start + start_flag:])
                # print('time for find one nalu end:', time.time() - previous_time)
                # print(end)
                # print(data[offset + start + end - 8: offset + start + end + 8])
                
                if end == -1:
                    end = len(data)
                else:
                    end = offset + start + end
                nalu = data[offset + start + start_flag:end + start_flag]
                # end_part = data[offset + start +4 + end: offset + start + end + 8]
                offset = end
                print('nalu length:', len(nalu), ' start with: ', nalu[:4].hex(), ' end with: ', nalu[-4:].hex())
                self.nalu_list.append(nalu)
                # self.send_rtp_packet(nalu, client_socket)
                # time.sleep(0.0002)  # Simulate frame interval
                print('time for nalu segmentation:', time.time() - previous_time)
                if len(self.nalu_list) > 10:
                    break

    def stream_video(self, client_socket):
        # print('start sending rtp')
           
        for nalu_for_sending in self.nalu_list:
            previous_time = time.time()
            self.send_rtp_packet(nalu_for_sending, client_socket)
            print('time for sending one nalu: ', time.time() - previous_time)

    def generate_rtsp_response(self, request_message, client_socket):
        lines = request_message.split('\n')
        request_line = lines[0].split()
        method = request_line[0]
        uri = request_line[1]
        cseq = None
        auth = None
        for line in lines:
            if line.startswith('CSeq:'):
                cseq = line.split()[1]
            if line.startswith('Authorization:'):
                auth = line
        if not auth and not self.auth_flag:
            response = (
                    f"RTSP/1.0 401 Unauthorized\r\n"
                    f"CSeq: {cseq}\r\n"
                    f"WWW-Authenticate: Digest realm=\"{self.realm}\", nonce=\"{self.nonce}\"\r\n"
                    f"\r\n"
                )
        elif auth and not self.auth_flag:
            self.auth_flag = self.validate_auth(auth)
            if not self.auth_flag:
                response = (
                    f"RTSP/1.0 401 Unauthorized\r\n"
                    f"CSeq: {cseq}\r\n"
                    f"WWW-Authenticate: Digest realm=\"{self.realm}\", nonce=\"{self.nonce}\"\r\n"
                    f"\r\n"
                )
        if self.auth_flag:
                if method == 'OPTIONS':
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Public: OPTIONS, DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, ANNOUNCE, RECORD, GET_PARAMETER, SET_PARAMETER, REDIRECT\r\n"
                        f"\r\n"
                    )
                elif method == 'DESCRIBE':
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"x-Accept-Dynamic-Rate: 1\r\n"
                        f"Content-Base: {uri}\r\n"
                        f"Cache-Control: must-revalidate\r\n"
                        f"Content-Length: 704\r\n"
                        f"Content-Type: application/sdp\r\n"
                        f"\r\n"
                        f"v=0"
                        f"o=- 2257977626 2257977626 IN IP4 0.0.0.0\r\n"
                        f"s=Media Server\r\n"
                        f"c=IN IP4 0.0.0.0\r\n"
                        f"t=0 0\r\n"
                        f"a=control:*\r\n"
                        f"a=packetization-supported:DH\r\n"
                        f"a=rtppayload-supported:DH\r\n"
                        f"a=range:npt=now-\r\n"
                        f"m=video 0 RTP/AVP 96\r\n"
                        f"a=control:trackID=0\r\n"
                        f"a=framerate:20.000000\r\n"
                        f"a=rtpmap:96 H264/90000\r\n"
                        f"a=fmtp:96 packetization-mode=1;profile-level-id=4D4033;sprop-parameter-sets=Z01AM6aAKID1+WbgICAoAAADAAgAAAMBRCAA,aO48gAA=\r\n"
                        f"a=recvonly\r\n"
                        f"m=audio 0 RTP/AVP 97\r\n"
                        f"a=control:trackID=1\r\n"
                        f"a=rtpmap:97 MPEG4-GENERIC/8000\r\n"
                        f"a=fmtp:97 streamtype=5;profile-level-id=1;mode=AAC-hbr;sizelength=13;indexlength=3;indexdeltalength=3;config=1588\r\n"
                        f"a=recvonly\r\n"
                        f"m=application 0 RTP/AVP 107\r\n"
                        f"a=control:trackID=4\r\n"
                        f"a=rtpmap:107 vnd.onvif.metadata/90000\r\n"
                        f"a=recvonly\r\n"
                    )
                elif method == 'SETUP':
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Session: 6039690362586;timeout=60\r\n"
                        f"Transport: RTP/AVP/UDP;unicast;client_port=5004-5005;server_port=22944-22945;ssrc=2E623BB6\r\n"
                        f"x-Dynamic-Rate: 1\r\n"
                    )
                elif method ==  'PLAY':
                    response = (
                        f"TSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Session: 702896865214\r\n"
                        f"RTP-Info: url=trackID=0;seq=48955;rtptime=252952379\r\n"
                    )
                    self.streaming = True
                    threading.Thread(target=self.stream_video, args=(client_socket, )).start()
        return response


    def create_receiver(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"RTSP server listening on {self.host}:{self.port}")

        client_socket, client_address = server_socket.accept()
        print(f"Client connected: {client_address}")
        # clients.append(client_socket)

        while True:
            try:
                print('listening for client')
                data = client_socket.recv(1024)
                request_message = data.decode()
                print('client data: ', request_message)
                if not data:
                    break
                response = self.generate_rtsp_response(request_message, client_socket)
                client_socket.sendall(response.encode())
            except Exception as e:
                print(f"Error handling client: {e}")
                break

if __name__ == '__main__':
    rtsp_sender = rtsp_sender_line()
    rtsp_sender.create_receiver()
