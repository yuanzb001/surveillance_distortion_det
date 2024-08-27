import re
import hashlib
import struct

def send_rtsp_request(sock, request):
    print(f'Sending RTSP request:\n{request}')
    sock.sendall(request.encode())
    response = sock.recv(4096)
    print(f'Received RTSP response:\n{response.decode()}')
    return response.decode()

def extract_field_value(field_name, response):
    # 构造查找模式，例如 'realm="xxx"'
    pattern = field_name + '="([^"]+)"'
    
    # 使用正则表达式搜索模式
    match = re.search(pattern, response)
    
    # 如果找到匹配项，则返回捕获的值
    if match:
        return match.group(1)
    else:
        return None
    
def md5hex(data):
    return hashlib.md5(data.encode()).hexdigest()

def extract_info_from_SETUP(response):
    return re.search(r'Session:\s*(\S+);timeout=(\d+)', response)

def parse_rtp_packet(packet):
    # RTP 数据包的前12个字节是固定头部
    header = struct.unpack_from('!BBHII', packet, 0)
    
    version = header[0] >> 6
    padding = (header[0] >> 5) & 0x01
    extension = (header[0] >> 4) & 0x01
    csrc_count = header[0] & 0x0F
    marker = (header[1] >> 7) & 0x01
    payload_type = header[1] & 0x7F
    sequence_number = header[2]
    timestamp = header[3]
    ssrc = header[4]

    # print(f"Version: {version}, Padding: {padding}, Extension: {extension}, CSRC Count: {csrc_count}")
    # print(f"Marker: {marker}, Payload Type: {payload_type}, Sequence Number: {sequence_number}, Timestamp: {timestamp}, SSRC: {ssrc}")

    header_length = 12 + (csrc_count * 4)
    
    payload_data = packet[header_length:]
    # print(len(packet), ' bytes packet receiver with ', len(payload_data), ' bytes paylaod')
    # if sequence_number < 400:
    #         print(sequence_number)
    # print(sequence_number)
    return payload_data, sequence_number, timestamp

def write_nalu_to_file(nal_list, output_file):
    with open(output_file, 'wb') as f:
        for nalu in nal_list:
            # 假设这是一个单一NALU模式的RTP负载
            start_code = b'\x00\x00\x00\x01'
            f.write(start_code)
            f.write(nalu)
# 假设rtp_payloads是一个包含RTP负载数据的列表
# write_nalu_to_file(nal_list, 'output_test_500RTP_5.h264')