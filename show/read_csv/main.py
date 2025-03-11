# import csv
# import ast
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
#
#
# class PointCloudVisualizer:
#     def __init__(self, csv_file):
#         self.data = self.load_data(csv_file)
#         self.current_frame = 0
#         self.fig = plt.figure(figsize=(10, 8))
#         self.ax = self.fig.add_subplot(111, projection='3d')
#         self.ax.set_xlabel('X')
#         self.ax.set_ylabel('Y')
#         self.ax.set_zlabel('Z')
#         self.scatter = None
#         self.animation = None
#
#     def load_data(self, filename):
#         data = []
#         with open(csv_file, 'r', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             next(reader)  # 跳过第一行
#             next(reader)  # 跳过第二行
#             for row in reader:
#                 try:
#                     # 解析点云数据
#                     point_cloud = ast.literal_eval(row[1])
#                     data.append(np.array(point_cloud))
#                 except (SyntaxError, IndexError) as e:
#                     print(f"Error parsing row: {e}")
#         return data
#
#     def update(self, frame):
#         self.ax.cla()  # 清除当前轴
#         self.ax.set_xlabel('X')
#         self.ax.set_ylabel('Y')
#         self.ax.set_zlabel('Z')
#
#         if self.current_frame < len(self.data):
#             frame_data = self.data[self.current_frame]
#             if len(frame_data) > 0:
#                 # 提取XYZ坐标
#                 x = frame_data[:, 0]
#                 y = frame_data[:, 1]
#                 z = frame_data[:, 2]
#
#                 # 设置动态范围
#                 self.ax.set_xlim([np.min(x) - 10, np.max(x) + 10])
#                 self.ax.set_ylim([np.min(y) - 10, np.max(y) + 10])
#                 self.ax.set_zlim([np.min(z) - 10, np.max(z) + 10])
#
#                 # 绘制散点图（根据速度值着色）
#                 sc = self.ax.scatter(x, y, z, c=frame_data[:, 3],
#                                      cmap='viridis', s=5)
#                 if self.scatter is None:
#                     self.scatter = sc
#                     self.fig.colorbar(sc, ax=self.ax, label='Velocity')
#
#             self.ax.set_title(f'Frame: {self.current_frame} ({len(frame_data)} points)')
#             self.current_frame += 1
#
#     def start_animation(self):
#         self.animation = FuncAnimation(
#             self.fig,
#             self.update,
#             interval=200,  # 200ms per frame = 5fps
#             save_count=len(self.data)
#         )
#         plt.show()
#
#
# if __name__ == "__main__":
#     csv_file = 'F:\\code\\rada\\script\\origin_data_to_csv\\data\\inside_outside_20250310_15-15-38_bak.csv'  # <-- 替换为你的CSV文件路径
#     # 使用示例（替换为你的csv文件路径）
#     visualizer = PointCloudVisualizer(csv_file)
#     visualizer.start_animation()
#     while True:
#         pass