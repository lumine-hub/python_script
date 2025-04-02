import sys
import serial
import time
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QLabel,
                             QMessageBox, QDesktopWidget)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont

class RecordingThread(QThread):
    update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, com_port, baud_rate, file_path):
        super().__init__()
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.file_path = file_path
        self._is_running = True

    def stop(self):
        self._is_running = False

    def process_raw_line(self, line):
        raw_frame = [x.strip() for x in line.strip().split(',') if x.strip() != '']

        if len(raw_frame) < 2:
            return []

        try:
            frame_index = int(raw_frame[0])
            point_num = int(raw_frame[1])
        except ValueError:
            return []

        data = raw_frame[2:]
        if len(data) < point_num * 5:
            return []

        frame = []
        for i in range(point_num):
            try:
                point_item = [int(data[5 * i + j]) for j in range(5)]
                frame.append(point_item)
            except (ValueError, IndexError):
                continue
        return frame

    def run(self):
        try:
            ser = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            with open(self.file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timeForPointcloud', 'frameInfo', 'total_point_num'])

                while self._is_running:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        timestamp = time.time()
                        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                        millis = int((timestamp - int(timestamp)) * 1000)
                        time_str = f"{time_str}.{millis:03d}"

                        frame = self.process_raw_line(line)
                        total_point_num = len(frame)

                        status = f'Time: {time_str}, Points: {total_point_num}'
                        self.update_signal.emit(status)

                        writer.writerow([time_str, str(frame), str(total_point_num)])
            ser.close()
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


class RadarRecorderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recording_thread = None
        self.initUI()
        self.record_count = 48
        self.setup_styles()

    def initUI(self):
        # 设置窗口的宽度和高度
        window_width = 1200
        window_height = 800

        # 获取屏幕的大小
        screen_rect = QDesktopWidget().availableGeometry()
        screen_center = screen_rect.center()

        # 计算窗口左上角的坐标
        x = screen_center.x() - (window_width // 2)
        y = screen_center.y() - (window_height // 2)

        # 设置窗口的位置和大小
        self.setGeometry(x, y, window_width, window_height)

        self.setWindowTitle('Radar Data Recorder')
        # self.setGeometry(100, 100, 600, 300)  # 增大窗口尺寸

        main_widget = QWidget()
        layout = QVBoxLayout()

        # 增大输入框尺寸
        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(40)  # 设置最小高度

        self.action_input = QLineEdit()
        self.action_input.setMinimumHeight(40)

        # 使用更大的字体
        font = QFont()
        font.setPointSize(15)

        # 用户名输入
        username_label = QLabel('用户名:')
        username_label.setFont(font)
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # 动作输入
        action_label = QLabel('动作类型:')
        action_label.setFont(font)
        layout.addWidget(action_label)
        layout.addWidget(self.action_input)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton('开始录制')
        self.stop_btn = QPushButton('停止录制')
        self.stop_btn.setEnabled(False)

        # 设置按钮尺寸和字体
        for btn in [self.start_btn, self.stop_btn]:
            btn.setMinimumSize(200, 50)  # 最小宽度200，高度50
            btn.setFont(font)

        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 状态栏
        self.status_label = QLabel('准备就绪')
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 设置布局间距
        layout.setSpacing(20)  # 控件间距
        layout.setContentsMargins(30, 30, 30, 30)  # 边距

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    def setup_styles(self):
        # 设置全局样式
        self.setStyleSheet("""
            QLabel {
                font-size: 36px;
            }
            QLineEdit {
                font-size: 36px;
                padding: 8px;
            }
            QPushButton {
                font-size: 36px;
                min-width: 120px;
                padding: 10px;
            }
            QStatusBar {
                font-size: 36px;
            }
        """)
    def validate_inputs(self):
        username = self.username_input.text().strip()
        action = self.action_input.text().strip()
        if not username or not action:
            QMessageBox.warning(self, 'Input Error', 'Username and Action fields are required!')
            return False
        return True

    def generate_filename(self):
        timestamp = time.time()
        time_str = time.strftime("%Y%m%d_%H-%M-%S", time.localtime(timestamp))
        millis = int((timestamp - int(timestamp)) * 1000)
        username = self.username_input.text().strip().replace(' ', '_')
        action = self.action_input.text().strip().replace(' ', '_')
        return f'./fall_bed_data3/pointCloud_{time_str}.{millis:03d}_{username}_{action}_count{self.record_count}.csv'

    def start_recording(self):
        if not self.validate_inputs():
            return

        file_path = self.generate_filename()
        self.recording_thread = RecordingThread(
            com_port='COM30',
            baud_rate=921600,
            file_path=file_path
        )

        self.recording_thread.update_signal.connect(self.update_status)
        self.recording_thread.error_signal.connect(self.show_error)
        self.recording_thread.finished_signal.connect(self.recording_finished)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # 更新状态栏，显示当前计数
        self.status_label.setText(f'Recording... (Count: {self.record_count})')
        self.recording_thread.start()
        # 递增计数
        self.record_count += 1


    def stop_recording(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop()
            self.recording_thread.wait()

    def recording_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f'Recording Stopped - Data Saved (Total: {self.record_count - 1})')

    def update_status(self, message):
        self.status_label.setText(message)

    def show_error(self, message):
        QMessageBox.critical(self, 'Error', message)
        self.recording_finished()

    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop()
            self.recording_thread.wait()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RadarRecorderGUI()
    window.show()
    sys.exit(app.exec_())