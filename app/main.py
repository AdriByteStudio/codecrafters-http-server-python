import socket  # noqa: F401
import sys
import threading
import gzip
from pathlib import Path


def handle_connection(connection, directory):
    buffer = b""
    while True:
        while b"\r\n\r\n" not in buffer:
            chunk = connection.recv(1024)
            if not chunk:
                connection.close()
                return
            buffer += chunk

        header_data, _, buffer = buffer.partition(b"\r\n\r\n")
        lines = header_data.split(b"\r\n")
        request_line = lines[0]
        method, path, _ = request_line.split(b" ")

        headers = {}
        for line in lines[1:]:
            name, _, value = line.partition(b": ")
            headers[name.lower()] = value

        content_length = int(headers.get(b"content-length", b"0"))
        while len(buffer) < content_length:
            buffer += connection.recv(1024)
        body, buffer = buffer[:content_length], buffer[content_length:]

        close_connection = headers.get(b"connection", b"").lower() == b"close"
        response_body = b""

        if path == b"/":
            response = b"HTTP/1.1 200 OK\r\n"
        elif path.startswith(b"/echo/"):
            response_body = path[len(b"/echo/"):]
            encodings = [e.strip() for e in headers.get(b"accept-encoding", b"").split(b",")]
            content_encoding_header = b""
            if b"gzip" in encodings:
                content_encoding_header = b"Content-Encoding: gzip\r\n"
                response_body = gzip.compress(response_body)
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + content_encoding_header
                + b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
            )
        elif path == b"/user-agent":
            response_body = headers.get(b"user-agent", b"")
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
            )
        elif path.startswith(b"/files/"):
            filename = path[len(b"/files/"):].decode()
            file_path = Path(directory) / filename
            if method == b"POST":
                file_path.write_bytes(body)
                response = b"HTTP/1.1 201 Created\r\n"
            elif file_path.is_file():
                response_body = file_path.read_bytes()
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/octet-stream\r\n"
                    b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
                )
            else:
                response = b"HTTP/1.1 404 Not Found\r\n"
        else:
            response = b"HTTP/1.1 404 Not Found\r\n"

        if close_connection:
            response += b"Connection: close\r\n"
        response += b"\r\n" + response_body

        connection.sendall(response)

        if close_connection:
            connection.close()
            return


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
