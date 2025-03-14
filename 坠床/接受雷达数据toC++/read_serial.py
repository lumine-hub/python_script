import serial
import socket
import struct
import time


def main(serial_port, tcp_ip, tcp_port, max_retries=5, retry_delay=5):
    # 初始化串口
    ser = serial.Serial(
        port=serial_port,
        baudrate=921600,  # 根据雷达实际波特率调整
        timeout=2
    )

    # 初始化 TCP 客户端
    tcp_socket = None
    retries = 0

    # 尝试连接到 TCP 服务器
    def connect_to_server():
        nonlocal retries, tcp_socket
        retries = 0
        while retries < max_retries:
            try:
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.connect((tcp_ip, tcp_port))
                print(f"成功连接到 {tcp_ip}:{tcp_port}")
                retries = 0  # 重置重试次数
                return True
            except Exception as e:
                print(f"TCP 连接失败: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"尝试重新连接... ({retries}/{max_retries})")
                    time.sleep(retry_delay)  # 等待一段时间后重试
                else:
                    print("达到最大重试次数，暂时无法连接到服务器")
                    return False

    # 初始连接
    if not connect_to_server():
        return  # 如果初始连接失败，退出程序

    try:
        while True:
            # 读取一行数据（假设以换行符结尾）
            line = ser.readline().decode('ascii', errors='ignore').strip()
            print(line)
            if not line:
                continue

            # 分割数据字段
            parts = line.split(',')
            if len(parts) < 2:
                continue

            try:
                # 解析帧头和点数
                frame_index = int(parts[0])
                point_num = int(parts[1])
                expected_length = 2 + 5 * point_num - 1

                # 构建二进制数据包
                try:
                    # 包头：帧索引 (uint32), 点数 (uint32)
                    header = struct.pack('<II', frame_index, point_num)

                    # 包体：每个点的数据 (5 个 int16)
                    points_data = bytearray()
                    for i in range(point_num):
                        base = 2 + i * 5
                        try:
                            x = int(parts[base])
                            y = int(parts[base + 1])
                            z = int(parts[base + 2])
                            vel = int(parts[base + 3])
                            snr = int(parts[base + 4])
                            points_data += struct.pack('<5h', x, y, z, vel, snr)
                        except (ValueError, IndexError) as e:
                            print(f"解析点云数据时出错（点 {i}）: {e}")
                            print(f"数据字段: {parts[base:base + 5]}")
                            break  # 如果某个点解析失败，终止整个数据包的构建

                    # 如果成功构建了数据包，则发送
                    if len(points_data) == point_num * 10:  # 每个点占用 10 字节 (5 * int16)
                        while True:
                            try:
                                tcp_socket.sendall(header + points_data)
                                break  # 发送成功，退出循环
                            except Exception as e:
                                print(f"发送数据失败: {e}")
                                print("尝试重新连接...")
                                if not connect_to_server():
                                    print("无法重新连接到服务器，跳过当前数据包")
                                    break  # 无法重新连接，跳过当前数据包
                    else:
                        print("数据包不完整，跳过发送")
                except Exception as e:
                    print(f"数据包构建失败: {e}")

            except ValueError as e:
                print(f"数据解析错误: {e}")
                continue

    except KeyboardInterrupt:
        print("用户中断")
    finally:
        ser.close()
        if tcp_socket:
            tcp_socket.close()


if __name__ == "__main__":
    main('COM30', '127.0.0.1', 7777, max_retries=3, retry_delay=2)