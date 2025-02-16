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

    host, port = extract_host_port_from_request(request.decode('latin1'))
    destination_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    destination_socket.connect((host, port))
    destination_socket.sendall(request)
    print("Request forwarded to the destination")
    response = b''
    while True:
        data = destination_socket.recv(1024)
        if not data:
            break
        else:
            response = response + data
        # print(response.decode('latin1'), end='')
    client_socket.sendall(response)
    if 'CONNECT' in request.decode():
        pass
    else:
        print(response.decode('latin1'))
        cursor.execute('insert into all_requests values (?,?,?)', (time.time(), request.decode(), response.decode('latin1')))
    cursor.close()
    database.commit()
    database.close()
    destination_socket.close()
    client_socket.close()

def extract_host_port_from_request(request):
    host_string_start = request.find('Host: ') + len('Host: ')
    host_string_end = request.find('\r\n', host_string_start)
    host_string = request[host_string_start:host_string_end]
    port = 80
    if ':' in host_string:
        host, port = host_string.split(':')
        port = int(port)
    else:
        host = host_string
    return host, port

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