import serial
import time
import csv
from tqdm import tqdm

BOX_MIN = [-50, 10, -30]
BOX_MAX = [50, 200, 50]


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


def recording_data(com_port, baud_rate, num_frame, file_path):
    # 打开串口
    ser = serial.Serial(com_port, baud_rate, timeout=1)

    # 打开 CSV 文件用于写入数据
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # 写入 CSV 文件的表头
        writer.writerow(['timeForPointcloud', 'frameInfo', 'total_point_num'])

        # 判断是否是无限记录模式
        if num_frame == 0:
            print("Recording data until the program is stopped...")
            while True:  # 无限循环
                line = ser.readline().decode('utf-8').strip()  # 读取一行数据并去掉尾部空白字符
                if line:  # 确保不为空行
                    # 获取当前时间戳，精确到毫秒
                    timestamp = time.time()
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                    millis = int((timestamp - int(timestamp)) * 1000)
                    time_str = f"{time_str}.{millis:03d}"

                    # 处理当前行，解析点云数据
                    frame = process_raw_line(line)
                    total_point_num = len(frame)

                    # 将时间戳和点云数据保存为 CSV 格式
                    print(f'Time: {time_str}, Total point num: {total_point_num}')
                    writer.writerow([time_str, str(frame), str(total_point_num)])
        else:
            # 使用 tqdm 显示进度条
            for _ in tqdm(range(num_frame), desc="Recording Data", unit="frame"):
                line = ser.readline().decode('utf-8').strip()  # 读取一行数据并去掉尾部空白字符
                if line:  # 确保不为空行
                    # 获取当前时间戳，精确到毫秒
                    timestamp = time.time()
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                    millis = int((timestamp - int(timestamp)) * 1000)
                    time_str = f"{time_str}.{millis:03d}"

                    # 处理当前行，解析点云数据
                    frame = process_raw_line(line)
                    total_point_num = len(frame)

                    # 将时间戳和点云数据保存为 CSV 格式
                    writer.writerow([time_str, str(frame), str(total_point_num)])
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

    # 获取当前时间戳，并格式化为合法的文件名，精确到毫秒
    timestamp = time.time()
    time_str = time.strftime("%Y%m%d_%H-%M-%S", time.localtime(timestamp))
    millis = int((timestamp - int(timestamp)) * 1000)
    time_str = f"{time_str}.{millis:03d}"
    file_path = f'./data2/inside_outside_{time_str}.csv'  # 保存路径

    # 调用 recording_data 函数开始录制数据并保存到 CSV 文件
    recording_data(com_port, baud_rate, num_frame, file_path)