import socket  # noqa: F401
import sys
import threading
from pathlib import Path


def handle_connection(connection, directory):
    request = connection.recv(1024)
    while b"\r\n\r\n" not in request:
        request += connection.recv(1024)

    header_data, _, body = request.partition(b"\r\n\r\n")
    lines = header_data.split(b"\r\n")
    request_line = lines[0]
    method, path, _ = request_line.split(b" ")

    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(b": ")
        headers[name.lower()] = value

    content_length = int(headers.get(b"content-length", b"0"))
    while len(body) < content_length:
        body += connection.recv(1024)

    if path == b"/":
        connection.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif path.startswith(b"/echo/"):
        echo_body = path[len(b"/echo/"):]
        encodings = [e.strip() for e in headers.get(b"accept-encoding", b"").split(b",")]
        content_encoding_header = b""
        if b"gzip" in encodings:
            content_encoding_header = b"Content-Encoding: gzip\r\n"
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            + content_encoding_header
            + b"Content-Length: " + str(len(echo_body)).encode() + b"\r\n"
            b"\r\n" + echo_body
        )
        connection.sendall(response)
    elif path == b"/user-agent":
        user_agent = headers.get(b"user-agent", b"")
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(user_agent)).encode() + b"\r\n"
            b"\r\n" + user_agent
        )
        connection.sendall(response)
    elif path.startswith(b"/files/"):
        filename = path[len(b"/files/"):].decode()
        file_path = Path(directory) / filename
        if method == b"POST":
            file_path.write_bytes(body[:content_length])
            connection.sendall(b"HTTP/1.1 201 Created\r\n\r\n")
        elif file_path.is_file():
            file_body = file_path.read_bytes()
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/octet-stream\r\n"
                b"Content-Length: " + str(len(file_body)).encode() + b"\r\n"
                b"\r\n" + file_body
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
