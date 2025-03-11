import sys
import csv
import ast
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

## 这个脚本的作用是从csv文件中读取电云数据并且展示在3D的图像中。


class PointCloudVisualizer(QMainWindow):
    def __init__(self, csv_file, fps=5):
        super().__init__()
        self.setWindowTitle("Point Cloud Visualizer")
        self.resize(800, 600)

        # 初始化Matplotlib图形
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, projection='3d')

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.frames_per_second = fps
        self.frame_interval = 1000 // self.frames_per_second

        # 读取CSV点云数据
        self.all_frames = self.load_pointcloud_data(csv_file)

        # 启动动画
        self.anim = FuncAnimation(self.fig, self.update_frame,
                                  frames=len(self.all_frames),
                                  interval=self.frame_interval,
                                  repeat=False)
        self.canvas.draw()

    def load_pointcloud_data(self, csv_file):
        all_frames = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            next(reader)
            for row in reader:
                pointcloud_list = ast.literal_eval(row[1])
                # for i in range(0, len(pointcloud_list), 5):
                #     frame = pointcloud_list[i:i + 5]
                all_frames.append(pointcloud_list)
        return all_frames

    def update_frame(self, frame_idx):
        self.ax.clear()
        frame = self.all_frames[frame_idx]

        xs, ys, zs, snrs = [], [], [], []
        for point in frame:
            if len(point) == 5:
                x, y, z, v, snr = point
                xs.append(x)
                ys.append(y)
                zs.append(z)
                snrs.append(snr)

        self.ax.scatter(xs, ys, zs, c=snrs, cmap='viridis', s=20)
        self.ax.set_xlim(-500, 800)
        self.ax.set_ylim(-500, 800)
        self.ax.set_zlim(-200, 200)
        self.ax.set_title(f"Frame {frame_idx + 1}/{len(self.all_frames)}")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PointCloudVisualizer(
        csv_file='F:\\code\\rada\\script\\origin_data_to_csv\\data\\inside_outside_20250310_15-15-38_bak.csv',
        fps=5
    )
    window.show()
    sys.exit(app.exec_())
