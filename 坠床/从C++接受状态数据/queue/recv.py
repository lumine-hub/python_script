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
    HEADER_SIZE = 4  # 2字节帧头 + 2字节总长度
    # 数据结构：tid (2字节), state (2字节), numPoints (4字节), posX, posY, posZ, velX, velY, velZ, accX, accY, accZ (每个4字节，共9个4字节)
    TARGET_STRUCT_FMT = '<HHIfffffffff'
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

            frame_header, total_len = struct.unpack('<HH', header_data)
            if frame_header != 0xAA55:
                print(f"[Server] Invalid frame header: {hex(frame_header)}")
                continue

            body = recv_exact(conn, total_len)
            if not body:
                print("[Server] Body receive failed.")
                break

            # 假设 body 的第一个字节表示 target 数量
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
                print(target_info)
                targets.append(target_info)
                offset += TARGET_STRUCT_SIZE

            # 将解析后的 target 数据放入队列中
            data_queue.put(targets)
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
        self.y_range = (0, 3)   # y轴显示范围：0 ~ 3m

    def update_targets(self, targets):
        self.targets = targets
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.white)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 坐标映射偏移量（坐标原点在下方中间）
        origin_x = width / 2
        origin_y = height - 50  # 留50像素底部空白

        # 设置字体
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        # === 坐标轴 ===
        axis_pen = QtGui.QPen(QtCore.Qt.gray, 1, QtCore.Qt.DashLine)
        painter.setPen(axis_pen)

        # X轴
        painter.drawLine(0, int(origin_y), width, int(origin_y))

        # Y轴
        painter.drawLine(int(origin_x), int(origin_y), int(origin_x), int(origin_y - self.y_range[1] * self.scale))

        # === 坐标刻度 ===
        painter.setPen(QtCore.Qt.darkGray)
        # X方向刻度（-5m~5m）
        for m in range(self.x_range[0], self.x_range[1] + 1):
            x_pos = origin_x + m * self.scale
            painter.drawLine(int(x_pos), int(origin_y - 5), int(x_pos), int(origin_y + 5))
            painter.drawText(int(x_pos) - 10, int(origin_y + 20), f"{m}m")

        # Y方向刻度（0~3m）
        for m in range(int(self.y_range[0]), int(self.y_range[1]) + 1):
            y_pos = origin_y - m * self.scale
            painter.drawLine(int(origin_x - 5), int(y_pos), int(origin_x + 5), int(y_pos))
            if m != 0:
                painter.drawText(int(origin_x + 8), int(y_pos + 5), f"{m}m")

        # === 目标点绘制 ===
        if self.targets:
            for target in self.targets:
                x = target['posX']
                y = target['posY']
                draw_x = origin_x + x * self.scale
                draw_y = origin_y - y * self.scale

                # 点大小
                radius = 8
                painter.setBrush(QtCore.Qt.red)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QtCore.QPointF(draw_x, draw_y), radius, radius)

                # 坐标文字
                painter.setPen(QtCore.Qt.black)
                text = f"x:{x:.2f}, y:{y:.2f}, z:{target['posZ']:.2f}"
                painter.drawText(int(draw_x + 10), int(draw_y), text)
        else:
            # 如果无目标，显示提示
            painter.setPen(QtCore.Qt.darkGray)
            painter.drawText(width / 2 - 50, height / 2, "暂无目标")



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Target Display")
        self.display_widget = TargetDisplayWidget(self)
        self.setCentralWidget(self.display_widget)

        # 使用定时器轮询数据队列，间隔 100ms 检查一次
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_queue)
        self.timer.start(100)

    def poll_queue(self):
        """定时器回调，检查队列中是否有新数据"""
        while not data_queue.empty():
            try:
                targets = data_queue.get_nowait()
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
