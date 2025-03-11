# 直接将点云数据录制成kinect那种格式的文件
import serial
import time
import csv
from tqdm import tqdm

BOX_MIN = [-50, 10, -30]
BOX_MAX = [50, 200, 50]

# 修改 process_raw_line 函数，使其能够处理从串口读取的每一行数据
# def process_raw_line(line):
#     print(line)
#     raw_frame = line.split(',')[:-1][2:]  # 去掉第一项和最后一项，获取数据
#     point_num = int(len(raw_frame) / 5)  # 每个点包含 5 个数据项
#     frame = []
#     for i in range(point_num):
#         point_item = [int(raw_frame[5*i + j]) for j in range(5)]  # 将每个点的数据转换为整数
#         frame.append(point_item)
#     return frame


def process_raw_line(line):
    print(line)
    # 拆分字符串并去掉多余空项（末尾多的逗号可能产生空字符串）
    raw_frame = [x.strip() for x in line.strip().split(',') if x.strip() != '']

    if len(raw_frame) < 2:
        print("行数据长度不足，跳过")
        return []

    try:
        frame_index = int(raw_frame[0])
        point_num = int(raw_frame[1])
    except ValueError:
        print("帧索引或点数解析失败，跳过")
        return []

    data = raw_frame[2:]

    if len(data) < point_num * 5:
        print(f"点云数据长度不足：实际={len(data)}，预期={point_num * 5}，跳过")
        return []

    frame = []
    for i in range(point_num):
        try:
            point_item = [int(data[5 * i + j]) for j in range(5)]
            frame.append(point_item)
        except (ValueError, IndexError):
            print(f"第 {i} 个点数据有误，跳过：{data[5 * i: 5 * i + 5]}")
            continue

    return frame


def cal_in_out_point_num(frame):
    # 计算每一帧对应在范围内和范围外点的数量
    in_point_num = 0
    out_point_num = 0
    for i in range(len(frame)):
        if frame[i][0] < BOX_MAX[0] and frame[i][1] < BOX_MAX[1] and frame[i][2] < BOX_MAX[2]:
            in_point_num += 1
        else:
            out_point_num += 1
    return in_point_num, out_point_num


# 修改下面的函数，当num_frame = 0的时候，一直记录数据，直到结束程序
def recording_data(com_port, baud_rate, num_frame, file_path):
    # 打开串口
    ser = serial.Serial(com_port, baud_rate, timeout=1)
    
    # 打开 CSV 文件用于写入数据
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # 写入 CSV 文件的表头
        writer.writerow(['timeForPointcloud', 'frameInfo', 'in_point_num', 'out_point_num'])
        
        # 判断是否是无限记录模式
        if num_frame == 0:
            print("Recording data until the program is stopped...")
            while True:  # 无限循环
                line = ser.readline().decode('utf-8').strip()  # 读取一行数据并去掉尾部空白字符
                if line:  # 确保不为空行
                    # 获取当前时间戳
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    
                    # 处理当前行，解析点云数据
                    frame = process_raw_line(line)
                    in_point_num, out_point_num = cal_in_out_point_num(frame)
                    
                    # 将时间戳和点云数据保存为 CSV 格式
                    print(f'Time: {time_str}, In point num: {in_point_num}, Out point num: {out_point_num}')
                    writer.writerow([time_str, str(frame), str(in_point_num), str(out_point_num)])
        else:
            # 使用 tqdm 显示进度条
            for _ in tqdm(range(num_frame), desc="Recording Data", unit="frame"):
                line = ser.readline().decode('utf-8').strip()  # 读取一行数据并去掉尾部空白字符
                if line:  # 确保不为空行
                    # 获取当前时间戳
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    
                    # 处理当前行，解析点云数据
                    frame = process_raw_line(line)
                    in_point_num, out_point_num = cal_in_out_point_num(frame)
                    
                    # 将时间戳和点云数据保存为 CSV 格式
                    writer.writerow([time_str, str(frame), str(in_point_num), str(out_point_num)])
    # 关闭串口
    ser.close()

if __name__ == '__main__':
    com_port = 'COM30'  # 根据实际情况设置串口
    baud_rate = 921600
    # baud_rate = 115200
    seconds = 30  # 录制60秒的数据
    fs = 15  # 每秒钟15帧
    # num_frame = seconds * fs  # 总帧数
    num_frame = 0
    
    # 获取当前时间戳，并格式化为合法的文件名
    time_str = time.strftime("%Y%m%d_%H-%M-%S", time.localtime())
    file_path = f'./data/inside_outside_{time_str}.csv'  # 保存路径
    
    # 调用 recording_data 函数开始录制数据并保存到 CSV 文件
    recording_data(com_port, baud_rate, num_frame, file_path)

#  20-40秒 走着， 40秒左右开始跌倒，跌倒50s

# 8:53的50分开始走动，8:54的00准时跌倒，10左右站起来

# 21-16-43  10秒开始跌倒， 0- 10 走动

# 09:09上床  10:10 - 10:15 离床后走动， 10:20多吧又坐上去
# 11:43 - 11:46离床，走动 12:10绕床走一圈