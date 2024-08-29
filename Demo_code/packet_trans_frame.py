import av
import os
import cv2
import time
import signal
import struct
import pyshark
import numpy as np
import pandas as pd
from multiprocessing import shared_memory
from network_util import parse_rtp_packet
# from problem_detect import distortion_detect
from text_detect_util import getTextfromFrame
from problem_detect import RTP_loss, P_slice_qp_value_extract, getFeatures, getRL
from problem_detect import blur_detector, noise_detector, badlight_detect, occlusion_detect

def decode_nalu(duration_break, nalu_list, timestamp_nalu_queue, qp_threshold, frame_packet, qp_list, stop_flag):
    print('wait for decoding h264 to frame!!!')
    previoustime = time.time()
    decoded_nalu_count = 0
    # 创建 PyAV 解码器上下文
    codec_context = av.CodecContext.create('h264', 'r')
    frame_count = 0
    start_code = b'\x00\x00\x00\x01'
    # with open('get_from_camera.h264', 'wb') as f:
    
    
    frame_duration = 0
    while True:
        if stop_flag.value:
            while not frame_packet.empty():
                frame_packet.get()
            while not nalu_list.empty():
                nalu_list.get()
            while not timestamp_nalu_queue.empty():
                timestamp_nalu_queue.get()
            break

        # print('nalu queue: ', nalu_list.qsize())
        previoustime = time.time()
        # print(nalu_list.empty())
        if not nalu_list.empty():
            # print('nalu list not empty!')
            nalu = nalu_list.get()
            # print('nalu length: ', len(nalu))
        else:
            time.sleep(0.5)
            continue
        if not timestamp_nalu_queue.empty():
            timestamp = timestamp_nalu_queue.get()
        # nalu = start_code + nalu
        # f.write(nalu)
        # 确保 NALU 片段以起始码开头


        if not nalu.startswith(start_code):
            nalu = start_code + nalu
        qp_value, nalu_type = P_slice_qp_value_extract(nalu[4:].hex())
        print(nalu_type)
        # print('time for find qp value: ', time.time() - previoustime)
        # print('nalu length:', len(nalu), ' start with: ', nalu[:4].hex(), ' end with: ', nalu[-4:].hex())
        if qp_value != -10000:
            qp_list.append((qp_value + 26))
            # print('***********************************************')
            # print(qp_value + 26)
            # print('***********************************************')
        # print('not start with start code!')
        # if decoded_nalu_count != duration_break:
        #     decoded_nalu_count += 1
        #     continue
        # else:
        #     decoded_nalu_count = 0
        # print('nalu length:', len(nalu), ' start with: ', nalu[:4])
        decode_flag = False
        
        if nalu_type in [5, 6, 7, 8] or frame_duration == duration_break:
            decode_flag = True
            frame_duration = 0
        else:
            frame_duration += 1
            print('frame duration: ', frame_duration)       
        
        if decode_flag:
            print('nalu type: ', nalu_type, ' with length: ', len(nalu))
            try:
                # 创建 PyAV 包
                # print(nalu[:10])
                # print(nalu[-10:])
                # print('nalu check: ', time.time() - previoustime)
                packet = av.Packet(nalu)
                # print('av Packet nalu: ', time.time() - previoustime)
                # 发送包到解码器
                frames = codec_context.decode(packet)
                # print('codec context: ', time.time() - previoustime)
                for frame in frames:
                    frame_count += 1
                    img = frame.to_ndarray(format='bgr24')
                    # print(str(frame_count) + '.jpg')
                    # cv2.imwrite(str(frame_count) + '.jpg', img)
                    frame_packet.put((timestamp, img))
                    # print('av process time: ', time.time() - previoustime)
            except av.AVError as e:
                print(f"Error decoding packet: {e}")
                time.sleep(0.5)
                continue
            # qp_value = P_slice_qp_value_extract(nalu_data.hex())
            # print('nalu length:', len(nalu_data), ' start with: ', nalu_data[:4].hex(), ' end with: ', nalu_data[-4:].hex())
            # if qp_value != -10000:
            #     qp_list.append((qp_value))

            time.sleep(0.0001)
            # print('got 1 frame: ', time.time() - previoustime)
            previoustime = time.time()


def continuous_packet_capture(interface, capture_filter, packet_queue, shared_array, shape, metadata, lock, stop_flag):
    
    capture = pyshark.LiveCapture(interface=interface, bpf_filter=capture_filter, tshark_path='C:/Users/Administrator/Wireshark/tshark.exe')
    
    print(f"Starting continuous packet capture on interface ...")
    # count = 0
    index = 0

    for packet in capture.sniff_continuously():

        if stop_flag.value:
            metadata[:] = []
            break

        # print(f"RTP Packet {packet.number}:")
        # print(packet.sniff_time)
        previoustime = time.time()
        udp_payload_hex = packet.udp.payload.replace(':', '')
        udp_payload_bytes = bytes.fromhex(udp_payload_hex)
        end_index = index + len(udp_payload_bytes)
        # print('end index before lock: ', end_index)
        if end_index >= len(shared_array):
            index = 0
        # if end_index < shared_array.size:
        # print(len(shared_array))
        with lock:
            # print('end index:', end_index)
            shared_array[index:index + len(udp_payload_bytes)] = udp_payload_bytes
            # print('store data:', end_index)
            metadata.append((index, len(udp_payload_bytes), packet.number))
            # print('store metadata')
        index += len(udp_payload_bytes)
        # print(index) 
        time.sleep(0.0001)
        # print('1 packet receiver time: ', time.time() - previoustime)

def extract_packet_to_nalu(packet_queue, nalu_queue, timestamp_nalu_queue, shared_array, shape, metadata, lock, packet_loss_list, stop_flag):
    file_path = 'bitstream_data/'
    seq_num_list = []
    print('extract start!!!!')
    nalu = bytearray()

    previoustime = time.time()
    packet_count = 0
    process_total = 0
    trans_total = 0
    wait_time = 0
    wait_count = 0
    index = 0
    target_timestamp = -1
    total_packet_rec = 0
    min_seq_num = -1
    last_seq_num = -1
    interval = 1

    codec_context = av.CodecContext.create('h264', 'r')
    frame_count = 0
    start_code = b'\x00\x00\x00\x01'

    while True:
        if stop_flag.value:
            metadata[:] = []
            while not nalu_queue.empty():
                nalu_queue.get()
            packet_loss_list[:] = []
            break
        previoustime_waitStart = time.time()
        previoustime_transStart = time.time()
        # print(len(metadata))
        if len(metadata) > 0:
            with lock:
                # print('lock in extract_packet_to_nalu')
                start_index, length, packet_number = metadata.pop(0)
                udp_payload_bytes = bytes(shared_array[start_index:start_index + length])
                for i in range(start_index, start_index + length):
                    shared_array[i] = 0
                # shared_array[start_index:start_index + length].fill(0)
            # print('unlock in extract_packet_to_nalu')
            packet_count += 1
            
            # print(len(udp_payload_bytes))    
        else:
            time.sleep(0.1)
            wait_count += 1
            wait_time += (time.time() - previoustime_waitStart)
            continue
        trans_total += (time.time() - previoustime_transStart)

        previoustime_process = time.time()
        raw_data, seq_num, timestamp = parse_rtp_packet(udp_payload_bytes)
        # print('timestamp: ', timestamp)
        file_path = file_path + str(timestamp) + '.h264'
        # timestamp_nalu_queue.put(timestamp)
        if target_timestamp == -1:
            target_timestamp = timestamp         
        else:
            if target_timestamp != timestamp:
                # timestamp_nalu_queue.put(timestamp)
                if len(seq_num_list)> 1:
                    interval = min(seq_num_list) - last_seq_num
                    packet_loss = RTP_loss(seq_num_list, interval)
                    # print('packet loss: ', packet_loss)
                    if packet_loss != 0:
                        packet_loss_list.append((target_timestamp, packet_loss))
                        print('timestamp: ', timestamp, ' with pakcet loss: ', packet_loss)
                        # print('len of packet loss list in extract: ', len(packet_loss_list))
                    last_seq_num = max(seq_num_list)
                else:
                    last_seq_num = seq_num_list[0]
                    interval = 1
                target_timestamp = timestamp
                total_packet_rec += len(seq_num_list)                              
                seq_num_list = []
        seq_num_list.append(seq_num)
        
        slice_flag = (raw_data[0] & 0x1F)
        # print(raw_data[0])
        # print(slice_flag)
        if slice_flag == 28:
            # print('FU-A type')
            fu_header = raw_data[1]
            start_bit = fu_header >> 7
            end_bit = (fu_header >> 6) & 0x01
            nal_header = (raw_data[0] & 0xE0) | (fu_header & 0x1F)
            # print(nal_header)
            # 起始片段
            if start_bit:
                print('nal Unit Start !!!!!!!!!!!!!!!!')
                nalu = bytearray([nal_header])  # 使用NALU头重建NALU
                # print('nalu header: ', nalu)
                nalu.extend(raw_data[2:])  # 添加负载数据
                start_found = True 
                timestamp_nalu_queue.put(timestamp)
            # 中间或结束片段
                process_total += (time.time() - previoustime_process)
            else:
                nalu.extend(raw_data[2:])
                # print(len(raw_data[2:]))
                if end_bit == 1:
                    print('nal Unit End !!!!!!!!!!!!!!!!')
                    nalu_queue.put(nalu)
                    frame_count += 1
                    print('frame count: ', frame_count)
                    # print('nalu length:', len(nalu))
                    process_total += (time.time() - previoustime_process)
                    # print('extract 1 nalu time: ', time.time() - previoustime)
                    # print('process 1 nalu time: ', process_total)
                    # print('transfer 1 nalu time: ', trans_total)
                    # print('wait ', wait_count, ' times for  1 nalu with time: ', wait_time)
                    wait_count = 0
                    wait_time = 0
                    trans_total = 0
                    process_total = 0
                    # print('total ', packet_count, ' packets')
                    packet_count = 0
                    previoustime = time.time()
                    # print(f"Captured packet: {len(nalu)} bytes")
                    # nalu_count += 1
                    # print(nalu_count, ' nalu with length ', len(nalu))
                    nalu = bytearray()        
        # elif slice_flag == 29:
        #     # print('FU-B')
        else:
            print('whole nalu in one packet')
            nalu_queue.put(raw_data)
            frame_count += 1
            print('frame count: ', frame_count)
            # print('not start with start code!')
            # print('nalu length:', len(nalu), ' start with: ', nalu[:4])
            # print('nalu length:', len(raw_data))
            process_total += (time.time() - previoustime_process)
            # print('extract 1 nalu time: ', time.time() - previoustime)
            # print('total ', packet_count, ' packets')
            # print('process 1 nalu time: ', process_total)
            # print('transfer 1 nalu time: ', trans_total)
            # print('wait ', wait_count, ' times for  1 nalu with time: ', wait_time)
            wait_count = 0
            wait_time = 0
            trans_total = 0
            packet_count = 0
            previoustime = time.time()
            # print(f"Captured packet: {len(raw_data)} bytes")
            # nalu_count += 1
        time.sleep(0.1) 
        # wait_count += 1
        # wait_time += (time.time() - previoustime_waitStart)

def frames_analysis(frame_queue, fps, packet_loss, qp_list, det_res_queue, stop_flag):
    """
    从帧队列中读取帧并显示。
    """
    print('prepare for frame analysis')
    QP_THRESHOLD = 30
    #######################################
    #### Counting variable
    frame_count = 0
    #######################################

    #######################################
    #### persistent variable
    frame_RL_list = []
    #######################################


    #######################################
    #### Previous record variable
    previous_RL = -1
    #######################################

    #######################################
    #### Detector configuration variable
    noise_unit = noise_detector()
    blur_unit = blur_detector()
    #######################################

    while True:
        beginning_time = time.time()
        if stop_flag.value:
            while not frame_queue.empty():
                frame_queue.get()
            qp_list[:] = []
            packet_loss[:] = [] 
            while not det_res_queue.empty():
                det_res_queue.get()
            break
        got_problem = False

        if not frame_queue.empty():
            timestamp, frame = frame_queue.get()
            #################################################
            ########## Frame info variable
            frame_count += 1
            problem_type = []   #1: packet loss; 2: compression; 3: occlusion; 4: badlight; 5: blur; 6: noise
            details_info = ''
            qp_list[:] = []
            #################################################


            previoustime = time.time()
            print('Main view shows: ', frame_count, ' frame show........................................')
            if frame is None:
                break
            
            start_time = time.time()
            ## Packet loss Detect part
            if len(packet_loss) != 0: 
                print('packet loss happened !!!!!!!!!!!!!!!!!!!!!!') 
                problem_type.append(1)
                    
                details_info = ''
                for time_info, loss_rate in packet_loss:
                    print('Main view shows: At the time ', time_info, ' with loss rate ', loss_rate)
                    # timestamp, problem_type, details, frames = det_res_queue.get()
                    # timestamp = time_info
                    details_info += 'At the time ' + str(time_info) + ' with loss rate ' + str(loss_rate) + '\n'
                
                ## delete all record
                packet_loss[:] = []
            print('time for calculating packet loss: ', time.time() - start_time)
            start_time = time.time()

            ## QP value detect part
            if len(problem_type) == 0 and len(qp_list) != 0:
                if qp_list[-1] > QP_THRESHOLD:
                    details_info = 'Main view shows: The qp of GOP is ' + str(qp_list[-1])
                    problem_type.append(2)
            print('time for qp detect: ', time.time() - start_time)
            start_time = time.time()

            # ## Error text detect
            # if len(problem_type) == 0:
            #     getTextfromFrame(frame)

            if len(problem_type) == 0:
                frame_RL = getRL(frame)
                frame_RL_list.append(frame_RL)

                print('time for extract RL: ', time.time() - start_time)
                start_time = time.time()

                if len(frame_RL_list) == 5:
                    if previous_RL == -1:
                        previous_RL = np.mean(frame_RL_list)
                    else:
                        occ_res, previous_RL = occlusion_detect(previous_RL, frame_RL_list)
                        if occ_res:
                            details_info = 'Has detected the occlusion problem!'
                            print(details_info)
                            problem_type.append(3)
                    frame_RL_list = []

                    print('time for detect occlusion: ', time.time() - start_time)
                    start_time = time.time()
                

                if len(problem_type) == 0:
                    badlight_res = badlight_detect(frame_RL)
                    image_features_blur, image_features_noise, black_area_ratio = getFeatures(frame)

                    print('time for detect badlight and extract features', time.time() - start_time)
                    start_time = time.time()

                    blur_res = blur_unit.predict_res(pd.DataFrame(image_features_blur, index=[0]))

                    print('time for predicting of blur: ', time.time() - start_time)
                    start_time = time.time()

                    noise_res = noise_unit.predict_res(pd.DataFrame(image_features_noise, index=[0]))
                    print('time for predicting of noise: ', time.time() - start_time)
                    start_time = time.time()
                    print('black area ratio: ', black_area_ratio)
                    if black_area_ratio > 0.9:
                        details_info += 'Has detected the black full background from camera!'
                        print(details_info)
                        problem_type.append(7)
                    elif badlight_res:
                        details_info += 'Has detected the Badlight condition for camera!'
                        print(details_info)
                        problem_type.append(4)
                    elif blur_res:
                        details_info += 'Has detected the Blur in the video!'
                        problem_type.append(5)
                        print(details_info)
                    elif noise_res:
                        details_info += 'Has detected the noise problem!'
                        problem_type.append(6)
                        print(details_info)
        
            print(frame.shape)
            det_res_queue.put((timestamp, problem_type, details_info, frame))
            print('whole analysis time for one frame: ', time.time() - beginning_time)

                        

                




                

            