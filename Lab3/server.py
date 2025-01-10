import socket
import threading
from datetime import datetime

# 构造GMT时间，格式仿照课本上HTTP报文时间格式：Thu，15 Feb 2023 15:44:04 GMT）
def get_gmt_time():
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# 大写转小写，小写转大写的函数
def transform(entity):
    return ''.join([char.lower() if char.isupper() else char.upper() for char in entity])

# 501的返回信息
def _501response():
    return ("FDUnet/1.0 501 Not Implemented\r\n"
            f"Date: {get_gmt_time()}\r\n"
            "\r\n")

# 200的返回信息
def _200response(transformed_data):
    return ("FDUnet/1.0 200 OK\r\n"
            f"Date: {get_gmt_time()}\r\n"
            "\r\n"
            f"{transformed_data}\r\n")

# 处理客户端内容
def handle_client(client_socket, client_address):
    print(f"Connection from {client_address} has been established.")
    while True:
        try:  # 接收客户端发来的数据
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break
            print(f"Received from {client_address}:\n{request}")
            lines = request.splitlines()  # 解析请求报文
            if len(lines) < 3:  # 请求格式错误，返回 501
                response = _501response()
            else:  # 检查请求行是否为 POST / 1.0
                if lines[0] == "POST / FDUnet/1.0":
                    entity = lines[-1]
                    if entity:  # 实体存在则返回 200 OK 和转换后的字符串
                        transformed_data = transform(entity)
                        response = _200response(transformed_data)
                    else:  # 如果没有实体内容，返回 501
                        response = _501response()
                else:  # 请求行不正确，返回 501
                    response = _501response()
            # 发送响应
            client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
            break

    # 关闭客户端连接
    client_socket.close()
    print(f"Connection with {client_address} closed.")

# 创建服务器
def start_server():
    # 创建 Socket，指定为 IPv4 和 TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定 Socket 到特定地址和端口
    # 相当于告诉网络协议栈自己的“门牌号”，其他程序就可以通过该地址和端口与指定的 Socket 通信。
    server_socket.bind(('127.0.0.1', 12000))
    # 服务器端开始监听端口，等待响应客户端发送的连接请求或数据。
    server_socket.listen(5)
    print("Server is listening on port 12000...")
    while True:
        # 接受客户端连接
        client_socket, client_address = server_socket.accept()
        # 为每个客户端创建一个新线程
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()


if __name__ == "__main__":
    start_server()
