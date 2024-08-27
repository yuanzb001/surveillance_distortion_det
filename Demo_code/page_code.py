import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QScrollArea, QTableWidget, QTableWidgetItem, 
    QDialog, QAbstractItemView)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt
# from control_mulitprocess import Video_Analysis

class VideoPlayer(QObject):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, video_path):
        super().__init__()
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
            self.frame_ready.emit(q_image)
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
        self.video_analysis = None
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)

        video_layout = QVBoxLayout()

        self.video_label = QLabel(self)
        self.video_label.setFixedSize(1920, 1080)
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
        scroll_area.setFixedHeight(150)  
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
        case1 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '3000', 'High Compression']
        case2 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '21000', 'Packet loss']
        case3 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '51000', 'Bad light condition']
        case4 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '90000', 'Blur']
        case5 = ['Camera 1', '/Users/zhuobinyuan/rtsp_test/demo_framework/sample_dataset_reencode.mp4', '111000', 'Camera shake']
        self.append_item(case1)
        self.append_item(case2)
        self.append_item(case3)
        self.append_item(case4)
        self.append_item(case5)

        self.table_widget.setColumnWidth(0, 100)  # 设置 "Camera ID" 列的宽度
        self.table_widget.setColumnWidth(1, 100)  # 设置 "Timestamp" 列的宽度
        self.table_widget.setColumnWidth(2, 300)  # 设置 "Problem" 列的宽度

        # 按钮
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_analysis)
        # self.start_button.setEnabled(False)
        self.end_button = QPushButton("Pause", self)
        self.end_button.clicked.connect(self.end_analysis)
        # self.end_button.setEnabled(False)

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
        right_layout.addWidget(self.store_button)
        right_layout.addWidget(self.clear_button)
        right_layout.addWidget(self.start_button)
        right_layout.addWidget(self.end_button)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setFixedWidth(500)

        # 将右边布局添加到主布局
        main_layout.addWidget(right_widget)

        # 设置窗口属性
        self.setLayout(main_layout)
        self.setWindowTitle('Automatic Diagnosis of Video Quality Problems')
        self.setGeometry(100, 100, 800, 400)
        self.show()

    def start_analysis(self):
        self.video_analysis = Video_Analysis()
        self.video_analysis.start_analysis()
        self.start_button.setEnabled(False)

    def end_analysis(self):
        if self.video_analysis != None:
            self.video_analysis.end_analysis()
            self.video_analysis = None
            self.start_button.setEnabled(True)

    def show_camera_list_dialog(self):
        dialog = CameraListDialog()
        dialog.exec_()

    def update_frame(self, q_image):
        self.video_label.setPixmap(QPixmap.fromImage(q_image))
    
    def store_record(self):
        print('store to file')

    def append_item(self, case1):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        item_camera_id = QTableWidgetItem(case1[0])
        item_camera_id.setData(Qt.UserRole,case1[1])
        self.table_widget.setItem(row_position, 0, item_camera_id)
        self.table_widget.setItem(row_position, 1, QTableWidgetItem(case1[2]))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem(case1[3]))

    def clear_items(self):
        self.table_widget.setRowCount(0)

    def upload_record(self):
        print('upload data from file')

    def row_item_clicked(self, row, column):
        camera_id_item = self.table_widget.item(row, 0)
        timestamp_item = self.table_widget.item(row, 1)
        problem_item = self.table_widget.item(row, 2)

        camera_id = camera_id_item.text()
        timestamp = timestamp_item.text()
        problem = problem_item.text()

        file_path = camera_id_item.data(Qt.UserRole)

        # print(f"Clicked row {row}: Camera ID={camera_id}, Timestamp={timestamp}, Problem={problem}")
        # print(f"Hidden Data: {hidden_data}")
        # print(f"Clicked item: {item.text()}")  # 输出被点击的项目文本
        if file_path != None:
            self.video_player = VideoPlayer(file_path)
            self.video_player.frame_ready.connect(self.update_frame)
            self.video_player.next_frame()
            self.play_button.clicked.connect(self.video_player.start)
            self.stop_button.clicked.connect(self.video_player.stop)
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)

    def closeEvent(self, event):
        self.video_player.release()
        event.accept()

# if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # window = MainWindow()
    # sys.exit(app.exec_())