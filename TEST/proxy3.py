import socket
import threading
import sqlite3
import signal
import sys
import time

def setup_database():
    database = sqlite3.connect('./Captured_requests.db')
    cursor = database.cursor()
    try:
        cursor.execute('drop table all_requests')
    except:
        pass
    cursor.execute('create table all_requests (Request_Number float, Request text, Response text)')
    database.close()

def handle_client_request(client_socket):
    database = sqlite3.connect('./Captured_requests.db')
    cursor = database.cursor()

    print("Received request:")
    request = b''
    client_socket.setblocking(False)
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            request += data
            print(data.decode('utf-8'), end='')
        except BlockingIOError:
            break

    host, port = extract_host_port_from_request(request)
    if host is None or port is None:
        print("Invalid host or port. Skipping connection attempt.")

    destination_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        destination_socket.connect((host, port))
    except OSError as e:
        print(f"OSError while connecting to {host}:{port} - {e}")

    destination_socket.sendall(request)
    print("Request forwarded to the destination")
    response = b''
    while True:
        data = destination_socket.recv(1024)
        if not data:
            break
        else:
            response = response + data
        # print(response.decode('utf-8'))), end='')
    client_socket.sendall(response)
    if 'CONNECT' in request.decode():
        pass
    else:
        print(response.decode('utf-8'))
        cursor.execute('insert into all_requests values (?,?,?)', (time.time(), request.decode(), response.decode('utf-8')))
    database.commit()
    cursor.close()
    database.close()
    destination_socket.close()
    client_socket.close()

def extract_host_port_from_request(request):
    try:
        host_string_start = request.find(b'Host: ') + len(b'Host: ')
        host_string_end = request.find(b'\r\n', host_string_start)
        host_string = request[host_string_start:host_string_end].decode('utf-8')
        print(f"Extracted host string: {host_string}")
        webserver_pos = host_string.find("/")
        if webserver_pos == -1:
            webserver_pos = len(host_string)
        port_pos = host_string.find(":")
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            host = host_string[:webserver_pos]
        else:
            port = int((host_string[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            host = host_string[:port_pos]
        print(f"Extracted host: {host}, port: {port}")
        return host, port
    except Exception as e:
        print(f"Exception while extracting host and port: {e}")
        return None, None


def start_proxy_server(port=8080):
    setup_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', port))
    server.listen(5)
    print(f"Proxy server running on port {port}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=handle_client_request, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_proxy_server()