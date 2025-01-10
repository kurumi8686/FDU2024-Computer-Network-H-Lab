import socket
import threading
import random
import time
import pickle
import os
import struct
BUF_SIZE = 1500
SERVER_IP = '127.0.0.1'
CLIENT_IP = '127.0.0.1'
PORT = 7777


class server_thread(threading.Thread):
    """Thread to handle each client connection."""
    def __init__(self, client_address, socket):
        super().__init__()
        self.client_address = client_address
        self.udp = UDP(client_address, Task('server.py'), None, None)
        self.socket = socket

    def run(self):
        """Run the thread to process client requests."""
        # Accept the client's connection request
        self.udp.recv_connect(self.socket)
        print('Connection successful!')
        if self.udp.mode == 'S':
            print('Preparing to receive data')
            # Notify client that the server is ready to receive
            self.udp.send_packet(self.udp.pack('', -1, -1, 'ready'))
            self.udp.recv()
        elif self.udp.mode == 'R':
            print('Preparing to send data')
            self.udp.send()
            self.udp.timeout = 0.2

        self.udp.task.finish()
        os.system("md5sum " + self.udp.file_name)


class Task:
    """Class to handle file transfer tasks."""
    def __init__(self, file_path):
        self.start_time = time.time()
        self.file_size = os.path.getsize(file_path)
        self.byte_count = 0

    def sendto(self, socket, data, address):
        """Send data using the provided socket."""
        self.byte_count += len(data)
        socket.sendto(data, address)

    def finish(self):
        """Calculate and print the goodput and score after finishing the transfer."""
        elapsed_time = time.time() - self.start_time
        print("传输总时间：", elapsed_time, 's')
        print("有效吞吐量（文件大小 / 传输时间）：", self.file_size / elapsed_time / 1024, 'KB/s')
        if self.byte_count > 0:
            print("流量利用率（文件大小 / 发送的总数据量）：", self.file_size / self.byte_count)
        else:
            print("没有发送任何数据，无法计算流量利用率。")


class UDP:
    """Class to manage TCP-like communication over UDP."""
    def __init__(self, address, task: Task, file_name, mode, timeout=2):
        self.window_size = 1  # Size of the sending window
        self.threshold = 10000  # Congestion threshold
        self.start_time = 0  # Start time for the transfer
        self.left_seq = 0  # Left sequence number
        self.address = address
        self.task = task
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file_name = file_name
        self.mode = mode
        self.buffer_size = BUF_SIZE  # Buffer size for receiving data
        self.timer = None
        self.timeout = timeout
        self.max_length = 1400  # Maximum data length per packet
        self.buffer = []  # Buffer to hold packets
        self.current_seq = 0  # Current sequence number
        self.num_resends = 0  # Count of resends
        self.total_sent_bytes = 0  # total of bytes
        self.rtt_sum = 0
        self.rtt_count = 0
        self.est_rtt = 0  # 估计的 RTT

    def connect(self):
        """Establish a connection with the client."""
        random_seq = random.randint(0, 10000)
        packet = self.pack('H', random_seq, -1, '')  # 发送hello，相当于握手
        self.buffer.append(packet)
        self.send_packet(packet)
        self.start_timer()
        packet = self.receive_packet()
        self.buffer.clear()
        self.stop_timer()
        self.timeout = 2 * (time.time() - self.start_time)
        print(self.timeout)
        self.address = (self.address[0], packet['data'])
        packet = self.pack(self.mode, -1, -1, self.file_name)
        self.send_socket.close()
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_packet(packet)
        self.buffer.append(packet)
        self.start_timer()

    def recv_connect(self, socket: socket.socket):
        """Handle incoming connection requests from clients."""
        self.send_socket = socket
        self.start_time = time.time()
        # 创建一个计时器线程，该线程会等待3秒后自动调用close_connection函数。
        self.timer = threading.Timer(3, self.close_connection)
        # 将线程设置为守护线程，意味着主程序结束时该线程也会随之终止。
        self.timer.setDaemon(True)
        self.timer.start()  # 开始计时
        packet, self.address = self.send_socket.recvfrom(self.buffer_size)
        self.timeout = 2 * (time.time() - self.start_time)
        packet = pickle.loads(packet)
        self.stop_timer()
        self.mode = packet['type']
        self.file_name = packet['data']

    def send_packet(self, packet):
        """Send a packet to the specified address."""
        self.task.sendto(self.send_socket, packet, self.address)

    def receive_packet(self):
        """Receive a packet from the socket."""
        return pickle.loads(self.send_socket.recv(self.buffer_size))

    @staticmethod
    def pack(packet_type, seq_num, ack_num, data):
        """Pack the given parameters into a pickle object."""
        packet_dict = {
            'type': packet_type,
            'seq': seq_num,
            'ack': ack_num,
            'data': data
        }
        return pickle.dumps(packet_dict)

    # 开启和结束传输时的计时器
    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.start_time = time.time()
        self.timer = threading.Timer(self.timeout, self.timeout_resend)
        self.timer.setDaemon(True)
        self.timer.start()

    def stop_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = None

    def recv(self):
        isfirst = True
        f = open(self.file_name, 'wb')
        self.current_seq = 0
        finish = False
        while True:
            try:
                ptk = self.receive_packet()
            except socket.timeout:
                # 如果超时，检查是否已完成
                if finish:
                    break
                continue  # 继续等待接收包

            if isfirst:
                self.buffer.clear()
                self.buffer = [None] * BUF_SIZE
                self.stop_timer()
                isfirst = False
            if 0 <= ptk['seq'] - self.current_seq < BUF_SIZE:
                self.buffer[ptk['seq'] - self.current_seq] = ptk
            for i in range(BUF_SIZE):
                if self.buffer[i] is None:
                    self.buffer = self.buffer[i:] + [None] * i
                    break
                ptk = self.buffer[i]
                self.current_seq += 1
                if ptk['type'] != 'E':
                    f.write(ptk['data'])
                else:
                    finish = True
                    break
                if i == BUF_SIZE - 1:
                    self.buffer = [None] * BUF_SIZE
            if self.current_seq % 100 == 0:
                print(self.current_seq)

            if finish:  # 结束时确认包发送
                ack_packet = self.pack('E', -1, self.current_seq, '')
                self.send_packet(ack_packet)
                self.stop_timer()  # 在结束时停止定时器
                break

            else:
                ack_packet = self.pack('', -1, self.current_seq, '')
                self.send_packet(ack_packet)

        f.close()
        print("File received successfully.")

    def send(self):
        """Send data to the client."""
        self.buffer.clear()
        self.stop_timer()
        with open(self.file_name, "rb") as file:
            self.task = Task(self.file_name)
            seq_num = 0
            self.num_resends = 0
            finish = False
            ack_receiver = recvAck(self)
            ack_receiver.start()
            print(self.timeout)
            while True:
                if self.timer is None:
                    self.start_timer()
                while seq_num < self.left_seq + self.window_size and not finish:
                    if seq_num % 10 == 0:
                        print(seq_num, self.left_seq, self.window_size, self.threshold)
                    data = file.read(self.max_length)
                    if data:
                        packet = self.pack('', seq_num, -1, data)
                        self.send_packet(packet)
                        self.total_sent_bytes += len(packet)
                        self.buffer.append(packet)
                        seq_num += 1
                    else:
                        packet = self.pack('E', seq_num, -1, '')
                        self.send_packet(packet)
                        self.total_sent_bytes += len(packet)
                        seq_num += 1
                        finish = True
                        break
                if finish:
                    file.close()
                    break
            print("Packet loss rate:", self.num_resends / (self.num_resends + seq_num))

    def resend_gbn(self):
        """Resend packets in the buffer using Go Back N strategy."""
        # GBN策略: 将整个窗口中的包都重传
        valid_packets = [pkt for pkt in self.buffer if pkt is not None]
        resend_count = min(len(valid_packets), self.window_size)
        if resend_count > 0:
            print(f'Resending {resend_count} packets starting from seq', pickle.loads(valid_packets[0])['seq'])
            self.num_resends += resend_count
            for packet in valid_packets[:resend_count]:
                self.send_packet(packet)

    def resend_sr(self):
        """Resend packets in the buffer using Selective Repeat strategy."""
        # SR重传策略: 只重传未被确认的包
        for i in range(len(self.buffer)-1):
            if self.buffer[i] is not None:  # 检查当前包是否有效
                seq_num = pickle.loads(self.buffer[i])['seq']
                if seq_num < self.left_seq:  # 如果序列号小于左窗口边界，表示已确认
                    continue
                print(f'Resending packet with seq {seq_num}')
                self.send_packet(self.buffer[i])  # 重传未确认的包
                self.num_resends += 1  # 增加重传计数

    def timeout_resend(self):
        """Handle timeout and resend packets."""
        print('Timeout, resending packets')
        self.stop_timer()  # 停止当前定时器，避免重复
        # TCP Reno拥塞控制（基于丢包）: 在超时时将阈值减为window大小的一半，窗口重置为1，开始重传
        self.threshold = max(1, self.window_size // 2)  # 缩小为window大小的一半
        self.window_size = 1
        # self.resend_gbn()  # 执行重传 gbn方法
        self.resend_sr()  # 执行重传 sr方法
        self.start_timer()  # 重启定时器

    def close_connection(self):
        """Close the connection and cleanup."""
        self.stop_timer()  # 停止定时器
        self.left_seq = 0
        self.buffer.clear()
        self.send_socket.close()
        print("Connection closed.")
        exit(0)


class recvAck(threading.Thread):
    """Thread to receive ACK packets from the client."""
    def __init__(self, udp: UDP):
        threading.Thread.__init__(self)
        self.udp = udp
        self.current_ack = -1
        self.num_acks = 0
        self.prev_ack = 0

    def run(self):
        """Run the ACK receiving loop."""
        while True:
            try:
                packet = pickle.loads(self.udp.send_socket.recv(self.udp.buffer_size))
                ack_num = packet['ack']
                if self.current_ack == -1:  # 第一个 ACK 到达
                    self.udp.start_time = time.time()  # 记录开始时间
                rtt = time.time() - self.udp.start_time  # 计算 RTT
                if self.udp.rtt_count < 10:  # 仅在前 10 次 ACK 中进行 RTT 计算
                    self.udp.rtt_sum += rtt
                    self.udp.rtt_count += 1
                    self.udp.est_rtt = self.udp.rtt_sum / self.udp.rtt_count  # 更新估计的 RTT
                else:
                    # 更新估计的 RTT 和偏差
                    alpha = 0.125  # 平滑因子
                    self.udp.est_rtt = (1 - alpha) * self.udp.est_rtt + alpha * rtt

                if ack_num % 20 == 0:
                    print('Received ACK:', ack_num)
                # 更新窗口和阈值的策略
                left = self.udp.left_seq
                if ack_num > left:
                    self.udp.stop_timer()
                    self.udp.left_seq = ack_num  # 更新左窗口边界
                    self.udp.buffer = self.udp.buffer[ack_num - left:]  # 移除已确认包
                    self.udp.start_timer()
                    # TCP Reno拥塞控制: 在无拥塞情况下增大窗口（拥塞避免）
                    # self.udp.window_size += 1  # 增加窗口大小
                    # TCP Vegas拥塞控制
                    # 基于延迟的窗口调整逻辑。TCP Vegas 会在 RTT 增加时减小窗口，在 RTT 降低时增大窗口。
                    if self.udp.est_rtt > self.udp.threshold:  # 如果 RTT 超过阈值，减小窗口
                        self.udp.window_size = max(1, self.udp.window_size - 1)
                    else:
                        self.udp.window_size += 1  # 否则增加窗口
                elif ack_num == left:
                    self.num_acks += 1  # 重复ACK计数
                    # TCP Reno拥塞控制: 检测3个重复ACK时，认为发生丢包
                    if self.num_acks >= 3:
                        self.udp.threshold = max(1, self.udp.window_size // 2)  # 缩小为window大小的一半
                        self.udp.window_size = self.udp.threshold + 3  # 缩小窗口
                        self.num_acks = 0
                        # self.udp.resend_gbn()
                        self.udp.resend_sr()
                        self.udp.start_timer()
                if packet['type'] == 'E':
                    print('End of transmission.')
                    self.udp.stop_timer()  # 停止定时器，防止超时重传
                    self.udp.close_connection()
                    break

            except socket.timeout:
                print("ACK receive timeout")
                continue  # 继续尝试接收


