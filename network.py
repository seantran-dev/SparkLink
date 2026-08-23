import socket
import threading


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

    def start_server(self, host, port):
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.server.bind(
            (host, port)
        )

        self.server.listen()

        print(
            f"Listening on {host}:{port}"
        )

        threading.Thread(
            target=self.accept_connections,
            daemon=True
        ).start()

    def accept_connections(self):
        while True:
            client, addr = self.server.accept()

            connection = Connection(
                client
            )

            print(
                f"Incoming connection from {addr}"
            )

            client.sendall(
                f"IDENTITY:{self.user_id}|{self.username}\n".encode()
            )

            threading.Thread(
                target=self.receive,
                args=(connection,),
                daemon=True
            ).start()

    def connect(self, host, port, user_id):

        if user_id in self.connections:
            print(
                f"Already connected to {user_id}"
            )
            return

        if self.user_id > user_id:
            print(
                f"Waiting for {user_id} to initiate connection."
            )
            return

        threading.Thread(
            target=self._connect,
            args=(host, port),
            daemon=True
        ).start()

    def _connect(self, host, port):
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(5)

        try:
            sock.connect(
                (host, port)
            )

            sock.settimeout(None)

            connection = Connection(
                sock
            )

            sock.sendall(
                f"IDENTITY:{self.user_id}|{self.username}\n".encode()
            )

            print(
                f"Connected to {host}:{port}"
            )

            threading.Thread(
                target=self.receive,
                args=(connection,),
                daemon=True
            ).start()

        except socket.timeout:
            print(
                f"Connection to {host}:{port} timed out."
            )
            sock.close()

        except ConnectionRefusedError:
            print(
                f"Connection refused by {host}:{port}."
            )
            sock.close()

        except OSError as e:
            print(
                f"Connection failed: {e}"
            )
            sock.close()

    def receive(self, connection):
        buffer = ""

        while True:
            try:
                data = connection.sock.recv(
                    4096
                )

                if not data:
                    break

                buffer += data.decode(
                    "utf-8"
                )

                while "\n" in buffer:
                    message, buffer = buffer.split(
                        "\n",
                        1
                    )

                    if not message:
                        continue

                    self.handle_message(
                        connection,
                        message
                    )

            except (
                ConnectionResetError,
                ConnectionAbortedError,
                BrokenPipeError,
                OSError
            ):
                print(
                    "Connection closed."
                )
                break

        if connection.user_id in self.connections:
            del self.connections[
                connection.user_id
            ]

        if self.on_disconnect:
            self.on_disconnect(
                connection
            )

    def handle_message(self, connection, message):
        if message.startswith("CHAT:"):
            text = message[5:]

            if self.on_message:
                self.on_message(
                    connection,
                    text
                )

        elif message == "TYPING":
            if self.on_typing:
                self.on_typing(
                    connection
                )

        elif message == "STOP_TYPING":
            if self.on_stop_typing:
                self.on_stop_typing(
                    connection
                )

        elif message.startswith("IDENTITY:"):
            identity = message[9:]

            parts = identity.split(
                "|",
                1
            )

            if len(parts) != 2:
                return

            connection.user_id = parts[0]
            connection.username = parts[1]

            self.connections[
                connection.user_id
            ] = connection
            print(
                "CONNECTION REGISTERED:",
                connection.user_id,
                connection.username
            )

            print(
                "ALL CONNECTIONS:",
                list(self.connections.keys())
            )

            print(
                f"Connected to {connection.username}"
            )

            if self.on_connection:
                self.on_connection(
                    connection,
                    connection.username
                )

    def send(self, user_id, message):
        connection = self.connections.get(
            user_id
        )

        if not connection:
            return False

        try:
            connection.sock.sendall(
                f"CHAT:{message}\n".encode()
            )

            return True

        except OSError:
            return False

    def send_typing(self, user_id):
        connection = self.connections.get(
            user_id
        )

        if connection:
            try:
                connection.sock.sendall(
                    "TYPING\n".encode()
                )
            except OSError:
                pass

    def send_stop_typing(self, user_id):
        connection = self.connections.get(
            user_id
        )

        if connection:
            try:
                connection.sock.sendall(
                    "STOP_TYPING\n".encode()
                )
            except OSError:
                pass