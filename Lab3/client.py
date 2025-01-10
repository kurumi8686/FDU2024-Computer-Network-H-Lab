import socket
from datetime import datetime

# 构造GMT时间
def get_gmt_time():
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# 创建客户端
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12000))
    print("Connected to server.")

    while True:
        # 输入实体部分的字符串
        message = input("Enter message to send (type '#quit' to exit): ")
        if message == '#quit':
            break
        request = (
            "POST / FDUnet/1.0\r\n"
            f"Date: {get_gmt_time()}\r\n"
            "\r\n"
            f"{message}\r\n"
        )
        client_socket.send(request.encode('utf-8'))
        # 接收来自服务器的响应
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Received from server:\n{response}")

    client_socket.close()


if __name__ == "__main__":
    start_client()
