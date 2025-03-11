import socket
import struct

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
    HEADER_SIZE = 4  # 2 bytes frame header + 2 bytes total length
    TARGET_STRUCT_FMT = '<HHIfffffffff'  # 11个字段：2+2+4+9*4 = 46 bytes
    TARGET_STRUCT_SIZE = struct.calcsize(TARGET_STRUCT_FMT)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(1)
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

            target_num = body[0]
            print(f"[Server] TargetNum: {target_num}")
            offset = 1

            for i in range(target_num):
                target_data = body[offset : offset + TARGET_STRUCT_SIZE]
                if len(target_data) != TARGET_STRUCT_SIZE:
                    print(f"[Server] Target data size mismatch.")
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

                print(f"  Target {i}: {target_info}")
                offset += TARGET_STRUCT_SIZE

    except Exception as e:
        print(f"[Server] Exception: {e}")
    finally:
        conn.close()
        server_sock.close()
        print("[Server] Server closed.")

if __name__ == "__main__":
    start_target_state_server()
