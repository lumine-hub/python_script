import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt, QTimer, QPointF

FRAME_HEADER = 0xAA55
TARGET_STRUCT_FORMAT = '<HHI fff fff fff'
TARGET_STRUCT_SIZE = struct.calcsize(TARGET_STRUCT_FORMAT)

class PointCloudGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Point Cloud Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.scale_factor = 5  # 缩放比例，方便显示

    def update_points(self, points):
        self.scene.clear()
        for point in points:
            tid, x, y, z = point
            ellipse = QGraphicsEllipseItem(x * self.scale_factor, -y * self.scale_factor, 6, 6)
            ellipse.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(ellipse)

            text = QGraphicsTextItem(f"tid:{tid}\n({x:.1f},{y:.1f},{z:.1f})")
            text.setPos(x * self.scale_factor + 5, -y * self.scale_factor + 5)
            self.scene.addItem(text)

def handle_packet(packet_data):
    target_num = struct.unpack_from('B', packet_data, 0)[0]
    points = []

    offset = 1
    for _ in range(target_num):
        target_data = packet_data[offset: offset + TARGET_STRUCT_SIZE]
        tid, state, numPoints, posX, posY, posZ, *_ = struct.unpack(TARGET_STRUCT_FORMAT, target_data)
        points.append((tid, posX, posY, posZ))
        offset += TARGET_STRUCT_SIZE
    return points

def start_tcp_server(gui_window, host='127.0.0.1', port=8899):
    def server_loop():
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((host, port))
        server_sock.listen(1)
        print(f"[TCP Server] Listening on {host}:{port}...")

        conn, addr = server_sock.accept()
        print(f"[TCP Server] Connected by {addr}")

        buffer = b''
        while True:
            data = conn.recv(1024)
            # print(data)
            if not data:
                print("客户端断开连接")
                break
            buffer += data

            while True:
                if len(buffer) < 4:
                    break
                header, length = struct.unpack_from('<HH', buffer, 0)
                if header != FRAME_HEADER:
                    print("帧头错误，丢弃一个字节")
                    buffer = buffer[1:]
                    continue
                if len(buffer) < 4 + length:
                    break
                body = buffer[4:4 + length]
                points = handle_packet(body)
                print(points)
                gui_window.update_points(points)
                buffer = buffer[4 + length:]

    from threading import Thread
    Thread(target=server_loop, daemon=True).start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PointCloudGUI()
    window.show()
    start_tcp_server(window)
    sys.exit(app.exec_())