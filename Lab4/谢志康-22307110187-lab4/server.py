from udp import *
import sys
import importlib
importlib.reload(sys)
packet_struct = struct.Struct('I1024s')

def test_port(port):
    """Check if the specified port is available."""
    try:
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        new_socket.bind((SERVER_IP, port))
        return new_socket
    except Exception as e:
        print(f"Port {port} is not available: {e}")
        return None

def get_new_socket():
    """Get a new socket on an available port."""
    port = random.randint(7778, 10000)
    new_socket = test_port(port)
    while new_socket is None:
        port = random.randint(7778, 10000)
        new_socket = test_port(port)
    return port, new_socket


if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, PORT))
    print(f"Server running on {SERVER_IP}: {PORT}")
    while True:
        packet, client_address = server_socket.recvfrom(BUF_SIZE)
        packet = pickle.loads(packet)
        if packet['type'] != 'H':
            continue
        port, new_socket = get_new_socket()
        client_thread = server_thread(client_address, new_socket)
        client_thread.start()
        # Inform the client of the allocated port
        response_packet = client_thread.udp.pack('B', -1, packet['seq'], port)
        server_socket.sendto(response_packet, client_address)
