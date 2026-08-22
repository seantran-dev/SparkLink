import socket
import threading


class Network:

    def __init__(self, user_id, username):
        self.sock = None
        self.server = None
        self.gui = None
        self.user_id = user_id
        self.username = username
        self.friend_name = "Unknown"
        self.friend_user_id = None
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

            print(
                f"Incoming connection from {addr}"
            )

            client.sendall(
                f"IDENTITY:{self.user_id}|{self.username}\n".encode()
            )

            threading.Thread(
                target=self.receive,
                args=(client,),
                daemon=True
            ).start()

    def connect(self, host, port):
        if self.sock is not None:
            print("Already connected.")
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
            self.sock = sock

            self.sock.sendall(
                f"IDENTITY:{self.user_id}|{self.username}\n".encode()
            )

            print(
                f"Connected to {host}:{port}"
            )

            threading.Thread(
                target=self.receive,
                args=(self.sock,),
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

    def receive(self, sock):
        buffer = ""

        while True:
            try:
                data = sock.recv(4096)

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
                        sock,
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

    def handle_message(self, sock, message):
        if message.startswith("CHAT:"):
            text = message[5:]

            if self.on_message:
                self.on_message(
                    sock,
                    text
                )

        elif message == "TYPING":
            if self.on_typing:
                self.on_typing(
                    sock
                )

        elif message == "STOP_TYPING":
            if self.on_stop_typing:
                self.on_stop_typing(
                    sock
                )

        elif message.startswith("IDENTITY:"):
            identity = message[9:]

            parts = identity.split(
                "|",
                1
            )

            if len(parts) != 2:
                return

            self.friend_user_id = parts[0]
            self.friend_name = parts[1]

            print(
                f"Connected to {self.friend_name}"
            )

            if self.on_connection:
                self.on_connection(
                    sock,
                    self.friend_name
                )

    def send(self, message):

        if self.sock is None:
            return False

        try:

            self.sock.sendall(
                f"CHAT:{message}\n".encode()
            )

            return True

        except OSError:

            return False

    def send_typing(self):
        if self.sock:
            self.sock.sendall(
                "TYPING\n".encode()
            )

    def send_stop_typing(self):
        if self.sock:
            self.sock.sendall(
                "STOP_TYPING\n".encode()
            )