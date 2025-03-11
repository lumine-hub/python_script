import sys
import socket
import struct
import threading
import queue
from PyQt5 import QtCore, QtWidgets, QtGui

# 全局数据队列，服务器线程将接收到的数据放入队列中，GUI定时轮询数据
data_queue = queue.Queue()

def recv_exact(sock, size):
    """确保接收指定长度的字节"""
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data

def start_target_state_server(host='127.0.0.1', port=8899):
    HEADER_SIZE = 8  # 2字节帧头 + 4字节frame_index + 2字节payload长度
    TARGET_STRUCT_FMT = '<HHIfffffffff'  # tid, state, numPoints, posX~accZ
    TARGET_STRUCT_SIZE = struct.calcsize(TARGET_STRUCT_FMT)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(3)
    print(f"[Server] Listening on {host}:{port}...")

    conn, addr = server_sock.accept()
    print(f"[Server] Connected from {addr}")

    try:
        while True:
            header_data = recv_exact(conn, HEADER_SIZE)
            if not header_data:
                print("[Server] Connection closed.")
                break

            # 修正：包含frame_index的解析
            frame_header, frame_index, total_len = struct.unpack('<H I H', header_data)
            if frame_header != 0xAA55:
                print(f"[Server] Invalid frame header: {hex(frame_header)}")
                continue

            body = recv_exact(conn, total_len)
            if not body:
                print("[Server] Body receive failed.")
                break

            target_num = body[0]
            targets = []
            offset = 1

            for i in range(target_num):
                target_data = body[offset : offset + TARGET_STRUCT_SIZE]
                if len(target_data) != TARGET_STRUCT_SIZE:
                    print("[Server] Target data size mismatch.")
                    break

                fields = struct.unpack(TARGET_STRUCT_FMT, target_data)
                target_info = {
                    'tid': fields[0],
                    'state': fields[1],
                    'numPoints': fields[2],
                    'posX': fields[3],
                    'posY': fields[4],
                    'posZ': fields[5],
                    'velX': fields[6],
                    'velY': fields[7],
                    'velZ': fields[8],
                    'accX': fields[9],
                    'accY': fields[10],
                    'accZ': fields[11],
                }
                targets.append(target_info)
                offset += TARGET_STRUCT_SIZE

            print(f"[Server] Frame #{frame_index}, targetNum={target_num}, targets={targets}")
            data_queue.put((frame_index, targets))  # 加上frame_index放入队列
    except Exception as e:
        print(f"[Server] Exception: {e}")
    finally:
        conn.close()
        server_sock.close()
        print("[Server] Server closed.")

def server_thread():
    """服务器线程入口函数"""
    start_target_state_server()

class TargetDisplayWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TargetDisplayWidget, self).__init__(parent)
        self.targets = []
        self.scale = 100  # 1米 = 100像素，可调
        self.x_range = (-5, 5)  # x轴显示范围：-5m ~ 5m
        self.y_range = (0, 7)   # y轴显示范围：0 ~ 7m
        self.__actionIndex = ['empty', '正常', '行走', '坐', '跌倒', '跌倒', '出边界']

    def update_targets(self, targets):
        self.targets = targets
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.white)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 绘制帧序号
        painter.setPen(QtCore.Qt.black)
        painter.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        painter.drawText(10, 25, f"Frame #{self.parent().frame_index}")

        width = self.width()
        height = self.height()

        origin_x = width / 2
        origin_y = height - 50  # 原点在底部中间

        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        # 坐标轴
        axis_pen = QtGui.QPen(QtCore.Qt.gray, 1, QtCore.Qt.DashLine)
        painter.setPen(axis_pen)

        painter.drawLine(0, int(origin_y), width, int(origin_y))  # X轴
        painter.drawLine(int(origin_x), int(origin_y), int(origin_x), int(origin_y - self.y_range[1] * self.scale))  # Y轴

        painter.setPen(QtCore.Qt.darkGray)
        for m in range(self.x_range[0], self.x_range[1] + 1):
            x_pos = origin_x + m * self.scale
            painter.drawLine(int(x_pos), int(origin_y - 5), int(x_pos), int(origin_y + 5))
            painter.drawText(int(x_pos) - 10, int(origin_y + 20), f"{m}m")

        for m in range(int(self.y_range[0]), int(self.y_range[1]) + 1):
            y_pos = origin_y - m * self.scale
            painter.drawLine(int(origin_x - 5), int(y_pos), int(origin_x + 5), int(y_pos))
            if m != 0:
                painter.drawText(int(origin_x + 8), int(y_pos + 5), f"{m}m")

        # 绘制目标
        if self.targets:
            for target in self.targets:
                x = target['posX']
                y = target['posY']
                draw_x = origin_x + x * self.scale
                draw_y = origin_y - y * self.scale

                radius = 8
                painter.setBrush(QtCore.Qt.red)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QtCore.QPointF(draw_x, draw_y), radius, radius)

                # 文本信息
                painter.setPen(QtCore.Qt.black)
                text1 = f"x:{x:.2f}, y:{y:.2f}, z:{target['posZ']:.2f}"

                # 状态映射
                state_index = target.get('state', 0)
                state_text = self.__actionIndex[state_index] if 0 <= state_index < len(self.__actionIndex) else "未知"
                text2 = f"状态: {state_text}"

                painter.drawText(int(draw_x + 10), int(draw_y), text1)
                painter.drawText(int(draw_x + 10), int(draw_y + 15), text2)
        else:
            painter.setPen(QtCore.Qt.darkGray)
            painter.drawText(width / 2 - 50, height / 2, "暂无目标")




class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Target Display")
        self.display_widget = TargetDisplayWidget(self)
        self.setCentralWidget(self.display_widget)
        self.frame_index = 0  # 新增：保存当前帧序号

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_queue)
        self.timer.start(100)

    def poll_queue(self):
        """定时器回调，检查队列中是否有新数据"""
        while not data_queue.empty():
            try:
                frame_index, targets = data_queue.get_nowait()
                self.frame_index = frame_index  # 保存帧序号
                self.setWindowTitle(f"Target Display - Frame #{self.frame_index}")  # 更新标题
                self.display_widget.update_targets(targets)
            except queue.Empty:
                break

if __name__ == "__main__":
    # 启动服务器线程（守护线程，退出时自动关闭）
    t = threading.Thread(target=server_thread, daemon=True)
    t.start()

    # 启动 PyQt 应用程序
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
