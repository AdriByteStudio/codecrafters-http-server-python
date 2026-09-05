import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    connection, _ = server_socket.accept() # wait for client
    request = connection.recv(1024)
    request_line = request.split(b"\r\n")[0]
    _, path, _ = request_line.split(b" ")

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
    else:
        connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    connection.close()


if __name__ == "__main__":
    main()
