import socket
import re
import time
from urllib.parse import urlparse
from network_util import send_rtsp_request, extract_field_value, md5hex, extract_info_from_SETUP

class RTSP_control_Unit:
    def __init__(self, uri):
        self.uri = uri
        # self.host = 'localhost'
        self.host = '192.168.60.101'
        self.port = 8554
        self.decode_uri()
        self.sock = None
        self.createRTSP_comm()
        self.rtsp_server = f"{self.host}:{self.port}"
        self.rtsp_stream_path = ''
        self.cseq = 1
        self.session_id = 0
        self.username = None
        self.password = None
        

    def set_user_pass(self, username, password):
        if username != '':
            self.username = username
            self.password = password

    def decode_uri(self):
        parsed_rui = urlparse(self.uri)
        self.host = parsed_rui.hostname
        self.port = parsed_rui.port
        print(self.host)

    def createRTSP_comm(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close_socket(self):
        if self.sock != None:
            self.sock.close()

    def option_request(self):
        options_rtsp_request = f"OPTIONS {self.uri} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
        response_message = send_rtsp_request(self.sock, options_rtsp_request)
        print('************ response for OPTIONS ************************\n')
        print(response_message)
        if not self.handle_server_response(response_message, options_rtsp_request):
            if self.username != None and self.password != None:
                realm = extract_field_value("realm", response_message)
                nonce = extract_field_value("nonce", response_message)
                HA1 = md5hex(f"{self.username}:{realm}:{self.password}")
                HA2 = md5hex(f"OPTIONS:{self.uri}")
                response_digest = md5hex(f"{HA1}:{nonce}:{HA2}")
                # 在RTSP请求中包含Authorization头部
                authorization_header = f'Authorization: Digest username="{self.username}", realm="{realm}", nonce="{nonce}", uri="{self.uri}", response="{response_digest}"\r\n'
                # 构造RTSP OPTIONS请求，包括认证头部
                auth_option_request = f"OPTIONS rtsp://{self.rtsp_server}/{self.rtsp_stream_path} RTSP/1.0\r\nCSeq: 1\r\n{authorization_header}\r\n"
                response_message = send_rtsp_request(self.sock, auth_option_request)
                print('************ response for OPTIONS ************************\n')
                print(response_message)
        return self.handle_server_response(response_message, options_rtsp_request)

    def describe_request(self):    
        describe_request = f"DESCRIBE rtsp://{self.rtsp_server}/{self.rtsp_stream_path} RTSP/1.0\r\nCSeq: {self.cseq}\r\nAccept: application/sdp\r\n\r\n"
        response_message = send_rtsp_request(self.sock, describe_request)
        print('************ response for DESCRIBE ************************\n')
        print(response_message)
        return self.handle_server_response(response_message, describe_request)

    def setup_request(self):
        self.cseq += 1
        setup_request = f"SETUP rtsp://{self.rtsp_server}/{self.rtsp_stream_path}/trackID=0 RTSP/1.0\r\nCSeq: {self.cseq}\r\nTransport: RTP/AVP;unicast;client_port=5004-5005\r\n\r\n"
        response_message = send_rtsp_request(self.sock, setup_request)
        print('************ response for SETUP ************************\n')
        print(response_message)
        return self.handle_server_response(response_message, setup_request)

    def play_request(self):
        play_request = f"PLAY rtsp://{self.rtsp_server}/{self.rtsp_stream_path} RTSP/1.0\r\nCSeq: {self.cseq}\r\nSession: {self.session_id}\r\n\r\n"
        response_message = send_rtsp_request(self.sock, play_request)
        print('************ response for PLAY ************************\n')
        print(response_message)
        return self.handle_server_response(response_message, play_request)
    
    def stop_request(self):
        play_request = f"STOP rtsp://{self.rtsp_server}/{self.rtsp_stream_path} RTSP/1.0\r\nCSeq: {self.cseq}\r\nSession: {self.session_id}\r\n\r\n"
        response_message = send_rtsp_request(self.sock, play_request)
        print('************ response for STOP ************************\n')
        print(response_message)
        return self.handle_server_response(response_message, play_request)

    def handle_server_response(self, response, request):
        # for option authorization
         # for setup extract session_id and timeout 
        if 'SETUP' in request:
            if 'OK' in response:
                match = extract_info_from_SETUP(response)
                if match:
                    self.session_id, timeout_str = match.groups()
                    self.timeout = int(timeout_str)
                    print("Session ID:", self.session_id)
                    print("Timeout:", self.timeout, "seconds")
        if 'OK' in response:
            return True
        else:
            return False
    
    def rtsp_comm_proess(self):
        if self.option_request():
            if self.describe_request():
                if self.setup_request():
                    return self.play_request()
        return False
    
    def RSTP_comm_unit(self):
        self.rtsp_comm_proess()
        while True:
            time.sleep(60)  # 每60秒发送一次KEEP-ALIVE
            keep_alive_request = f"OPTIONS rtsp://{self.rtsp_server}/{self.rtsp_stream_path} RTSP/1.0\r\nCSeq: 3\r\nSession: 12345678\r\n\r\n"
            response = send_rtsp_request(self.sock, keep_alive_request)
            # print(response.decode())
            if not self.handle_server_response(response, keep_alive_request):
                break