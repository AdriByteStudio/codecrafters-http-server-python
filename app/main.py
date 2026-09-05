import socket  # noqa: F401
import sys
import threading
from pathlib import Path


def handle_connection(connection, directory):
    request = connection.recv(1024)
    lines = request.split(b"\r\n")
    request_line = lines[0]
    _, path, _ = request_line.split(b" ")

    headers = {}
    for line in lines[1:]:
        if not line:
            break
        name, _, value = line.partition(b": ")
        headers[name.lower()] = value

    if path == b"/":
        connection.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif path.startswith(b"/echo/"):
        body = path[len(b"/echo/"):]
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )
        connection.sendall(response)
    elif path == b"/user-agent":
        body = headers.get(b"user-agent", b"")
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )
        connection.sendall(response)
    elif path.startswith(b"/files/"):
        filename = path[len(b"/files/"):].decode()
        file_path = Path(directory) / filename
        if file_path.is_file():
            body = file_path.read_bytes()
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/octet-stream\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"\r\n" + body
            )
            connection.sendall(response)
        else:
            connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    else:
        connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    connection.close()


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    directory = None
    if "--directory" in sys.argv:
        directory = sys.argv[sys.argv.index("--directory") + 1]

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        connection, _ = server_socket.accept() # wait for client
        threading.Thread(target=handle_connection, args=(connection, directory)).start()


if __name__ == "__main__":
    main()
