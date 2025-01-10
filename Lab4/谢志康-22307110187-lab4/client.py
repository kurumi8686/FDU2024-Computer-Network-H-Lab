from udp import *
packet_struct = struct.Struct('I1024s')

if __name__ == "__main__":
    mode = input("Please input mode('S' for sending, 'R' for receiving): ")
    file_name = input("Please input your file name: ")
    task = Task('client.py')
    udp = UDP((CLIENT_IP, PORT), task, file_name, mode)
    udp.connect()
    if mode == 'S':
        print("Sending file...")
        udp.send()  # Send the file
    elif mode == 'R':
        print("Receiving file...")
        udp.recv()  # Receive the file
    else:
        print("please restart this process and input correct mode!")

    udp.task.finish(file_name)
