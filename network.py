import socket
from pathlib import Path
import threading

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Connection:
    def __init__(self, sock, user_id=None, username=None):
        self.sock = sock
        self.user_id = user_id
        self.username = username
        self.address = sock.getpeername()


class Network:
    def __init__(self, user_id, username):
        self.server = None
        self.gui = None
        self.user_id = user_id
        self.username = username
        self.connections = {}
        self.on_connection = None
        self.on_message = None
        self.on_typing = None
        self.on_stop_typing = None
        self.on_disconnect = None
        self.on_file_received = None

    # Server
    def start_server(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        print(f"Listening on {host}:{port}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            try:
                client, addr = self.server.accept()
                connection = Connection(client)
                print(f"Incoming connection from {addr}")
                client.sendall(f"IDENTITY:{self.user_id}|{self.username}\n".encode())
                threading.Thread(target=self.receive, args=(connection,), daemon=True).start()
            except OSError:
                break

    # Connect
    def connect(self, host, port, user_id):
        if user_id in self.connections:
            print(f"Already connected to {user_id}")
            return
        threading.Thread(target=self._connect, args=(host, port), daemon=True).start()

    def _connect(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((host, port))
            sock.settimeout(None)
            connection = Connection(sock)
            sock.sendall(f"IDENTITY:{self.user_id}|{self.username}\n".encode())
            print(f"Connected to {host}:{port}")
            threading.Thread(target=self.receive, args=(connection,), daemon=True).start()
        except socket.timeout:
            print(f"Connection to {host}:{port} timed out.")
            sock.close()
        except ConnectionRefusedError:
            print(f"Connection refused by {host}:{port}.")
            sock.close()
        except OSError as e:
            print(f"Connection failed: {e}")
            sock.close()

    # Receive
    def receive(self, connection):
        buffer = b""

        while True:
            try:
                data = connection.sock.recv(4096)
                if not data:
                    break
                buffer += data

                while True:
                    newline = buffer.find(b"\n")
                    if newline == -1:
                        break

                    header = buffer[:newline].decode("utf-8")
                    buffer = buffer[newline + 1:]

                    if not header:
                        continue

                    if header.startswith("FILE_START:"):
                        parts = header[11:].split("|", 1)
                        if len(parts) != 2:
                            continue

                        filename = Path(parts[0]).name
                        try:
                            file_size = int(parts[1])
                        except ValueError:
                            continue

                        success, buffer = self.receive_file(
                            connection, filename, file_size, buffer
                        )
                        if not success:
                            return
                        continue

                    self.handle_message(connection, header)

            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
                print("Connection closed.")
                break

        if connection.user_id in self.connections:
            if self.connections[connection.user_id] is connection:
                del self.connections[connection.user_id]

        if self.on_disconnect:
            self.on_disconnect(connection)

    # Receive file
    def receive_file(self, connection, filename, file_size, buffer):
        file_path = DOWNLOAD_DIR / filename
        counter = 1

        while file_path.exists():
            file_path = DOWNLOAD_DIR / f"{Path(filename).stem}_{counter}{Path(filename).suffix}"
            counter += 1

        bytes_received = 0

        try:
            with open(file_path, "wb") as file:
                while bytes_received < file_size:
                    if buffer:
                        remaining = file_size - bytes_received
                        chunk = buffer[:remaining]
                        buffer = buffer[len(chunk):]
                    else:
                        chunk = connection.sock.recv(min(4096, file_size - bytes_received))
                        if not chunk:
                            return False, buffer

                    file.write(chunk)
                    bytes_received += len(chunk)

            print(f"Received file: {file_path}")

            if self.on_file_received:
                self.on_file_received(connection, str(file_path), filename, file_size)

            return True, buffer

        except OSError as e:
            print(f"File receive failed: {e}")
            return False, buffer

    # Handle messages
    def handle_message(self, connection, message):
        if message.startswith("CHAT:"):
            if self.on_message:
                self.on_message(connection, message[5:])

        elif message == "TYPING":
            if self.on_typing:
                self.on_typing(connection)

        elif message == "STOP_TYPING":
            if self.on_stop_typing:
                self.on_stop_typing(connection)

        elif message.startswith("IDENTITY:"):
            parts = message[9:].split("|", 1)
            if len(parts) != 2:
                return

            connection.user_id = parts[0]
            connection.username = parts[1]

            existing = self.connections.get(connection.user_id)
            if existing is not None and existing is not connection:
                try:
                    existing.sock.close()
                except OSError:
                    pass

            self.connections[connection.user_id] = connection
            print(f"Connected to {connection.username}")

            if self.on_connection:
                self.on_connection(connection, connection.username)

    # Send message
    def send(self, user_id, message):
        connection = self.connections.get(user_id)
        if not connection:
            return False

        try:
            connection.sock.sendall(f"CHAT:{message}\n".encode())
            return True
        except OSError:
            return False

    # Send file
    def send_file(self, user_id, file_path):
        connection = self.connections.get(user_id)
        if not connection:
            return False

        path = Path(file_path)
        if not path.exists() or path.suffix.lower() not in (".jpg", ".jpeg", ".pdf"):
            return False

        try:
            file_size = path.stat().st_size
            filename = path.name
            header = f"FILE_START:{filename}|{file_size}\n".encode()
            connection.sock.sendall(header)

            with open(path, "rb") as file:
                while chunk := file.read(4096):
                    connection.sock.sendall(chunk)

            print(f"Sent file: {filename}")
            return True

        except OSError as e:
            print(f"File send failed: {e}")
            return False

    # Typing
    def send_typing(self, user_id):
        connection = self.connections.get(user_id)
        if connection:
            try:
                connection.sock.sendall("TYPING\n".encode())
            except OSError:
                pass

    def send_stop_typing(self, user_id):
        connection = self.connections.get(user_id)
        if connection:
            try:
                connection.sock.sendall("STOP_TYPING\n".encode())
            except OSError:
                pass