import threading
import multiprocessing
import av
import os
import sys
import csv
import cv2
import time
import queue
import asyncio
import pyshark
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from rtsp_control import RTSP_control_Unit
from rtp_data_receiver import RTP_receiver
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import shared_memory, Lock
from page_code import MainWindow
# from cv2_display_test import display_frames
from rtp_data_receiver import RTP_start
from packet_trans_frame import decode_nalu, continuous_packet_capture, extract_packet_to_nalu, frames_analysis

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QScrollArea, QTableWidget, QTableWidgetItem, 
    QDialog, QAbstractItemView, QFileDialog, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt, pyqtSlot, QThread

problem_type_dic = {
    1: 'packet loss',
    2: 'compression',
    3: 'occlusion',
    4: 'badlight',
    5: 'blur',
    6: 'noise'
}

class frame_record_update():
    def __init__(self):
        self.out = None
        self.sample_out = None
        self.previous_distortion = -1

    def run(self, det_res_queue, fps, table_items, stop_flag, frame_count):
        print('video store process!')
        pre_timestamp = -1
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'mp4v' 是 MP4 的编码器
        count = 0
        while True:
            # self.sample_out = cv2.VideoWriter('sample_video.mp4', fourcc, fps, (1920, 1080))
            if stop_flag.value:
                while not det_res_queue.empty():
                    det_res_queue.get()
                if self.out != None:
                    self.out.release()
                    self.out = None
                # if self.sample_out != None:
                #     self.sample_out.release()
                #     self.sample_out = None   
                break
            if not det_res_queue.empty():
                # frame_count += 1
                count += 1
                print('count of det_res_queue:' , count)
                timestamp, problem_type, details, frame = det_res_queue.get()
                if self.previous_distortion == -1 or self.previous_distortion != problem_type:
                    self.previous_distortion = problem_type
                    if self.out != None:
                        print('close the cv2 out because of problem type with -1')
                        self.out.release()
                        self.out = None
                        continue
                    frame_height, frame_width = frame.shape[:2]
                    now = datetime.now()
                    formatted_now = now.strftime("%Y%m%d_%H_%M_%S")
                    video_file_name = 'camera_1_' + formatted_now + str(timestamp) + '_' + problem_type_dic[problem_type[0]] +'.mp4'
                    sample_image_name = 'camera_1_' + formatted_now + str(timestamp) + '_' + problem_type_dic[problem_type[0]] +'.jpg'
                    detail_info_file = 'camera_1_' + formatted_now + str(timestamp) + '_' + problem_type_dic[problem_type[0]] +'.txt'
                
                    self.out = cv2.VideoWriter(video_file_name, fourcc, fps, (frame_width, frame_height))
                    cv2.imwrite(sample_image_name, frame)    
                    with open(detail_info_file, 'a', encoding='utf-8') as file:
                        file.write(details)

                    row_data = ['Camera 1', video_file_name, timestamp, problem_type_dic[problem_type[0]], detail_info_file]
                    table_items.put(row_data)
        
                # for frame in frames:
                self.out.write(frame)
                    # self.sample_out.write(frame)
                

                # if problem_type == -1:
                #     if self.out != None:
                #         print('close the cv2 out because of problem type with -1')
                #         self.out.release()
                #         self.out = None
                #         continue
                # print('timestamp of det_res_queue:' , timestamp)
                # if len(frames) > 0:
                #     frame_count.value += len(frames)
                #     frame_height, frame_width = frames[0].shape[:2]
                #     if pre_type == -1 or pre_timestamp != timestamp or self.pre_type != problem_type:
                #         if self.out != None:
                #             self.out.release()
                #             print('close the cv2 out becasue of the pre_type!!!!')
                #             self.out = None
                #         now = datetime.now()
                #         print("Current date and time:", now)
                #         formatted_now = now.strftime("%Y%m%d_%H_%M_%S")
                #         video_file_name = 'camera_1_' + formatted_now + str(timestamp) + '_' + problem_type_dic[problem_type] +'.mp4'
                #         detail_info_file = 'camera_1_' + formatted_now + str(timestamp) + '_' + problem_type_dic[problem_type] +'.txt'
                #         with open(detail_info_file, 'a', encoding='utf-8') as file:
                #             file.write(details)
                #         row_data = ['Camera 1', video_file_name, timestamp, problem_type_dic[problem_type], detail_info_file]
                #         table_items.put(row_data)
                #         # self.data_ready.emit(row_data)
                        
                #         self.out = cv2.VideoWriter(video_file_name, fourcc, fps, (frame_width, frame_height))
                #         pre_timestamp = timestamp
                #         pre_type = problem_type
                #     for frame in frames:
                #         self.out.write(frame)
                #         self.sample_out.write(frame)
                # time.sleep(0.01)
                
                

    def close_video_stream(self):
        if self.out != None:
            self.out.release()
            self.out = None

class VideoPlayer(QObject):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, video_path):
        super().__init__()
        video_path = os.path.join(os.getcwd(), video_path)
        # print(video_path)
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print("Error: Cannot open video.")
            sys.exit()
            
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def start(self):
        self.timer.start(30)  # 30ms interval for ~30fps

    def stop(self):
        self.timer.stop()

    def next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled_image = q_image.scaled(960, 540, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.frame_ready.emit(scaled_image)
        else:
            self.stop()

    def release(self):
        self.cap.release()

class CameraListDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)

        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(3)
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Camera ID", "IP Address"])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置只允许整行选中


        camera_ids = ["Camera 1", "Camera 2", "Camera 3"]
        ip_addresses = ["192.168.1.101", "192.168.1.102", "192.168.1.103"]

        for row in range(3):
            self.table_widget.setItem(row, 0, QTableWidgetItem(camera_ids[row]))
            self.table_widget.setItem(row, 1, QTableWidgetItem(ip_addresses[row]))

        main_layout.addWidget(self.table_widget)

        # 右边信息显示区域
        self.info_area = QPlainTextEdit(self)
        self.info_area.setReadOnly(True)
        main_layout.addWidget(self.info_area)

        self.setLayout(main_layout)
        self.setWindowTitle("Camera List")
        self.setGeometry(200, 200, 600, 400)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.video_player = None
        self.initUI()
        self.initControlParam()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_table_data)
        self.reload = False
        self.detect_flag = False

    def initUI(self):
        main_layout = QHBoxLayout(self)

        video_layout = QVBoxLayout()

        self.video_label = QLabel(self)
        self.video_label.setFixedSize(960, 540)
        video_layout.addWidget(self.video_label)

        control_layout = QHBoxLayout()
        self.play_button = QPushButton("Play", self)
        self.play_button.setEnabled(False)
        # self.play_button.clicked.connect(self.start_video)
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setEnabled(False)
        # self.stop_button.clicked.connect(self.end_video)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)

        video_layout.addLayout(control_layout)
        main_layout.addLayout(video_layout)

        right_layout = QVBoxLayout()

        id_ip_layout = QHBoxLayout()
        self.id_label = QLabel("ID: Camera 1", self)
        self.ip_label = QLabel("IP: 127.0.0.1", self)
        id_ip_layout.addWidget(self.id_label)
        id_ip_layout.addWidget(self.ip_label)

        right_layout.addLayout(id_ip_layout)

        self.camera_info_label = QLabel("Camera information:")
        right_layout.addWidget(self.camera_info_label)
        self.info_area = QPlainTextEdit(self)
        self.info_area.setReadOnly(True)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.info_area)
        scroll_area.setFixedHeight(100)  
        right_layout.addWidget(scroll_area)

        self.camera_list_button = QPushButton("Camera List", self)
        self.camera_list_button.clicked.connect(self.show_camera_list_dialog)
        right_layout.addWidget(self.camera_list_button)

        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(0)  # 初始化没有行
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Camera ID", "Timestamp", "Problem"])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置只允许整行选中
        right_layout.addWidget(self.table_widget)
        self.table_widget.cellClicked.connect(self.row_item_clicked)
        # case1 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '3000', 'High Compression']
        # case2 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '21000', 'Packet loss']
        # case3 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '51000', 'Bad light condition']
        # case4 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '90000', 'Blur']
        # case5 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '111000', 'Camera shake']
        # self.append_item(case1)
        # self.append_item(case2)
        # self.append_item(case3)
        # self.append_item(case4)
        # self.append_item(case5)

        self.frame_count_label = QLabel("Analysised frames count: ", self)
        self.frame_count = QLabel("0", self)
        frames_count_hbox = QHBoxLayout()
        frames_count_hbox.addWidget(self.frame_count_label)
        frames_count_hbox.addWidget(self.frame_count)

        right_layout.addLayout(frames_count_hbox)

        # 按钮
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_button_analysis)
        # self.start_button.setEnabled(False)
        self.end_button = QPushButton("Pause", self)
        self.end_button.clicked.connect(self.end_button_analysis)
        # self.end_button.setEnabled(False)

        right_layout.addWidget(self.start_button)
        right_layout.addWidget(self.end_button)

        self.table_widget.setColumnWidth(0, 75)  # 设置 "Camera ID" 列的宽度
        self.table_widget.setColumnWidth(1, 75)  # 设置 "Timestamp" 列的宽度
        self.table_widget.setColumnWidth(2, 175)  # 设置 "Problem" 列的宽度

        self.problem_info_label = QLabel("Problem Details:")
        right_layout.addWidget(self.problem_info_label)
        self.problem_info_area = QPlainTextEdit(self)
        self.problem_info_area.setReadOnly(True)
        problem_scroll_area = QScrollArea(self)
        problem_scroll_area.setWidgetResizable(True)
        problem_scroll_area.setWidget(self.problem_info_area)
        problem_scroll_area.setFixedHeight(100)  
        right_layout.addWidget(problem_scroll_area)


        # 新的按钮
        self.store_button = QPushButton("Download Record", self)
        self.store_button.clicked.connect(self.store_record)
        self.clear_button = QPushButton("Clear Record", self)
        self.clear_button.clicked.connect(self.clear_items)
        self.review_button = QPushButton("Review Downloaded Record", self)
        self.review_button.clicked.connect(self.upload_record)

        # 将控件添加到右边布局
        # right_layout.addWidget(username_label)
        # right_layout.addWidget(self.username_input)
        # right_layout.addWidget(password_label)
        # right_layout.addWidget(self.password_input)
        # right_layout.addWidget(ip_label)
        # right_layout.addWidget(self.ip_input)
        # right_layout.addWidget(self.list_widget)
        
        right_layout.addWidget(self.clear_button)
        right_layout.addWidget(self.review_button)
        right_layout.addWidget(self.store_button)
        

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setFixedWidth(375)

        # 将右边布局添加到主布局
        main_layout.addWidget(right_widget)

        # 设置窗口属性
        self.setLayout(main_layout)
        self.setWindowTitle('Automatic Diagnosis of Video Quality Problems')
        self.setGeometry(100, 100, 1500, 800)
        self.show()

    def start_button_analysis(self):
        if self.table_widget.rowCount() != 0 and not self.reload:
            reply = QMessageBox.question(self, 'Confirmation', 'Do you want to save the changes?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.store_record()
            else:
                self.clear_items()
        # self.video_analysis = Video_Analysis()
        self.detect_flag = True
        self.reload = False
        self.start_analysis()
        self.start_button.setEnabled(False)
        self.update_thread = frame_record_update()
        self.timer.start(1000)
        # self.table_widget.setDisabled(True)
        # self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # self.update_thread.data_ready.connect(self.update_table_data)
        # self.update_thread_process = multiprocessing.Process(target=self.update_thread.run, args=(self.det_res_queue, self.fps))
        # self.update_thread_process.start()

    def end_button_analysis(self):
        # if self.video_analysis != None:
        #     self.video_analysis.end_analysis()
        #     self.video_analysis = None
        self.detect_flag = False
        self.start_button.setEnabled(True)
        self.end_multiprocess()
        self.timer.stop()
        # self.table_widget.setDisabled(False)
        # self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # if self.update_thread_process != None and self.update_thread_process.is_alive():
        #     self.update_thread_process.terminate()
        #     self.update_thread.close_video_stream()
        print('end')

    def show_camera_list_dialog(self):
        dialog = CameraListDialog()
        dialog.exec_()

    def update_table_data(self):
        self.frame_count.setText(str(self.frame_count_value.value))
        # print('ready for table item update!')
        while not self.table_item_queue.empty():
            data = self.table_item_queue.get()
            print('row data: ', data[0], data[1], data[2], data[3])
            self.append_item(data)

    def update_frame(self, q_image):
        self.video_label.setPixmap(QPixmap.fromImage(q_image))
    
    def store_record(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "alksjflaksjfl", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                # 写入表头
                writer.writerow([self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())] + ["Video_file_path"] + ["Details_file_path"])
                # 写入表格数据
                for row in range(self.table_widget.rowCount()):
                    row_data = [self.table_widget.item(row, col).text() for col in range(self.table_widget.columnCount())]
                    hidden_data_1 = self.table_widget.item(row, 0).data(Qt.UserRole)
                    hidden_data_2 = self.table_widget.item(row, 2).data(Qt.UserRole)
                    writer.writerow(row_data + [hidden_data_1] + [hidden_data_2])
        print('store to file')

    def append_item(self, case):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        item_camera_id = QTableWidgetItem(case[0])
        item_camera_id.setData(Qt.UserRole,case[1])
        self.table_widget.setItem(row_position, 0, item_camera_id)
        # print('case[2]:', case[2])
        self.table_widget.setItem(row_position, 1, QTableWidgetItem(str(case[2])))
        item_problem_type = QTableWidgetItem(case[3])
        item_problem_type.setData(Qt.UserRole,case[4])
        self.table_widget.setItem(row_position, 2, item_problem_type)

    def clear_items(self):
        self.table_widget.setRowCount(0)
        self.problem_info_area.clear()

    def upload_record(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, 'r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader)  # 读取表头
                self.table_widget.setColumnCount(len(headers) - 2)  # 不包括隐藏数据列
                self.table_widget.setHorizontalHeaderLabels(headers[:-2])
                self.table_widget.setRowCount(0)  # 清空表格

                for row_data in reader:
                    row_position = self.table_widget.rowCount()
                    self.table_widget.insertRow(row_position)
                    for col, data in enumerate(row_data[:-2]):  # 不包括隐藏数据列
                        # print(col)
                        item = QTableWidgetItem(data)
                        self.table_widget.setItem(row_position, col, item)
                    # 设置隐藏数据
                    self.table_widget.item(row_position, 0).setData(Qt.UserRole, row_data[-2])
                    self.table_widget.item(row_position, 2).setData(Qt.UserRole, row_data[-1])
                self.reload = True

        print('upload data from file')

    def row_item_clicked(self, row, column):
        camera_id_item = self.table_widget.item(row, 0)
        timestamp_item = self.table_widget.item(row, 1)
        problem_item = self.table_widget.item(row, 2)

        camera_id = camera_id_item.text()
        timestamp = timestamp_item.text()
        problem = problem_item.text()
        video_file_path = None
        video_file_path = camera_id_item.data(Qt.UserRole)
        sample_image_name = video_file_path.replace('.mp4', '.jpg')
        details_file_path = None
        details_file_path = os.path.join(os.getcwd(),problem_item.data(Qt.UserRole))
        # print(f"Clicked row {row}: Camera ID={camera_id}, Timestamp={timestamp}, Problem={problem}")
        # print(f"Hidden Data: {hidden_data}")
        # print(f"Clicked item: {item.text()}")  # 输出被点击的项目文本
        if not self.detect_flag:
            if video_file_path != None:
                self.video_player = VideoPlayer(video_file_path)
                self.video_player.frame_ready.connect(self.update_frame)
                self.video_player.next_frame()
                self.play_button.clicked.connect(self.video_player.start)
                self.stop_button.clicked.connect(self.video_player.stop)
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
            if details_file_path != None:
                # print(details_file_path)
                with open(details_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    # 读取文件内容，并移除每行的换行符
                    # content = ''.join([line.strip() + '\n' for line in file])
                    content = file.read()
                    self.problem_info_area.setPlainText(content)
        else:
            print('！！！！！！！！！！！！！！！！！！！！！！！！！sample_image_name:', sample_image_name)
            frame = cv2.imread(sample_image_name)
            # self.video_label.setPixmap(QPixmap.fromImage(q_image))
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled_image = q_image.scaled(960, 540, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # self.frame_ready.emit(scaled_image)
            self.video_label.setPixmap(QPixmap.fromImage(scaled_image))

    def closeEvent(self, event):
        # self.video_player.release()
        event.accept()

    def initControlParam(self):
        ########## part of scatch network package
        self.interface = "lo0"  # 替换为你的网络接口名称
        self.capture_filter = "udp port 5004"  # 可选的捕获过滤器条件
        # capture_filter = "udp and src host 192.168.60.101"
        # display_filter = "ip.src == 192.168.1.10"  # 可选的显示过滤器条件
        self.packet_queue = multiprocessing.Queue(maxsize=1000)
        self.nalu_queue = multiprocessing.Queue(maxsize= 600)
        self.timestamp_nalu_queue = multiprocessing.Queue(maxsize= 600)
        self.frame_queue = multiprocessing.Queue(maxsize=100)
        self.det_res_queue = multiprocessing.Queue(maxsize=200)
        self.table_item_queue = multiprocessing.Queue(maxsize=200)
        
        self.fps = 50
        self.seq_num_list = []
        self.duration_break = 5

        self.rtp_receiver = None

        self.packet_size = 1410
        self.num_packets = 1000
        self.qp_threshold = 30

        self.shape = (int(self.packet_size * self.num_packets * 1.2),)  # 设置共享内存的大小，增加20%的余量
        self.shared_array = multiprocessing.Array('B', int(self.shape[0]))

        manager = multiprocessing.Manager()
        self.metadata = manager.list()
        self.packet_loss_list = manager.list()
        self.qp_list = manager.list()
        # loop = asyncio.get_event_loop()
        # executor = ThreadPoolExecutor(max_workers=2)

        # capture_Task = loop.create_task(continuous_packet_capture(interface, capture_filter, packet_queue))
        # capture_task = loop.run_in_executor(executor, continuous_packet_capture, interface, capture_filter, packet_queue)
        self.capture_process = None
        self.extract_process = None
        self.decode_process = None

        self.uri = 'rtsp://127.0.0.1:8554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        self.rtp_port = 5004
        self.rtsp_unit = None

        self.rtp_process = None 

        self.update_unit = frame_record_update()
        self.update_process = None
        self.video_stop_flag = multiprocessing.Value('b', False)
        self.frame_count_value = multiprocessing.Value('i', 0)

    def clear_queue(self, queue_input):
        while not queue_input.empty():
            queue_input.get()

    def start_analysis(self):
        self.video_stop_flag.value = False
        self.lock = Lock()
        self.clear_queue(self.packet_queue)
        self.clear_queue(self.nalu_queue)
        self.clear_queue(self.timestamp_nalu_queue)
        self.clear_queue(self.frame_queue)
        self.clear_queue(self.det_res_queue)
        self.clear_queue(self.table_item_queue)

        self.metadata[:] = []
        self.packet_loss_list[:] = []
        self.qp_list[:] = []

        self.capture_process = multiprocessing.Process(target=continuous_packet_capture, args=(self.interface, self.capture_filter, self.packet_queue, self.shared_array, self.shape, self.metadata, self.lock, self.video_stop_flag))
        self.extract_process = multiprocessing.Process(target=extract_packet_to_nalu, args=(self.packet_queue, self.nalu_queue, self.timestamp_nalu_queue, self.shared_array, self.shape, self.metadata, self.lock, self.packet_loss_list, self.video_stop_flag))
        self.decode_process = multiprocessing.Process(target=decode_nalu, args=(self.duration_break, self.nalu_queue, self.timestamp_nalu_queue, self.qp_threshold, self.frame_queue, self.qp_list, self.video_stop_flag))
        self.analysis_process = multiprocessing.Process(target=frames_analysis, args=(self.frame_queue, self.fps, self.packet_loss_list, self.qp_list, self.det_res_queue, self.video_stop_flag))
        self.update_process = multiprocessing.Process(target=self.update_unit.run, args=(self.det_res_queue, self.fps, self.table_item_queue, self.video_stop_flag, self.frame_count_value))
        

        self.extract_process.start()
        self.capture_process.start()  
        self.decode_process.start()
        self.analysis_process.start()
        self.update_process.start()
        time.sleep(5)
        ########## part of network communication
        # uri = 'rtsp://192.168.60.101:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        # uri = 'rtsp://127.0.0.1:8554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        # rtp_port = 5004      
        self.rtp_receiver = RTP_receiver(self.rtp_port)
        # rtp_process = multiprocessing.Process(target = rtp_receiver.receive_start)

        try:
            self.rtp_process = multiprocessing.Process(target=self.rtp_receiver.receive_start)
            
        except:
            print('error to rtp connection')
        self.rtp_process.start()
        try:
            self.rtsp_unit = RTSP_control_Unit(self.uri)
        
            self.rtsp_unit.set_user_pass('admin', 'Bearcat$')

            self.rtsp_process = multiprocessing.Process(target = self.rtsp_unit.RSTP_comm_unit)
            self.rtsp_process.start()
        except:
            print('error to rtsp communicate')
        
        

        ########## part of video show
        # self.frames_analysis(self.frame_queue, self.fps, self.packet_loss_list, self.qp_list)
        # self.extract_process.join()
        # self.capture_process.join()
        # self.decode_process.join()
        # self.analysis_process.join()

    def end_multiprocess(self):
        print(self.capture_process.is_alive())
        # if self.extract_process.is_alive():
        #     self.extract_process.terminate()
        # if self.capture_process.is_alive():
        #     self.capture_process.terminate()
        #     self.capture_process.join()
        # if self.decode_process.is_alive():
        #     self.decode_process.terminate()
        # if self.analysis_process.is_alive():
        #     self.analysis_process.terminate()
        if self.rtp_process.is_alive():
            self.rtp_process.terminate()
        if self.rtsp_process.is_alive():
            self.rtsp_process.terminate()
        # if self.update_process.is_alive():
        #     self.update_process.terminate()
        self.video_stop_flag.value = True
        self.update_unit.close_video_stream()
        self.rtp_receiver.close_socket()
        self.rtsp_unit.close_socket()
        

if __name__ == "__main__":
    # main()
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

