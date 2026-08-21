import socket
import threading

from protocol import Protocol


DEFAULT_PORT = 5000


class Connection:

    def __init__(
        self,
        sock,
        address,
        username
    ):

        self.sock = sock
        self.address = address
        self.username = username

        self.remote_username = None

        self.running = True

        self.on_message = None
        self.on_typing = None
        self.on_stop_typing = None
        self.on_username = None
        self.on_disconnect = None

        self.send_lock = threading.Lock()

    # =========================================================
    # START RECEIVING
    # =========================================================

    def start(self):

        threading.Thread(
            target=self.receive_loop,
            daemon=True
        ).start()

    # =========================================================
    # RECEIVE
    # =========================================================

    def receive_loop(self):

        try:

            while self.running:

                message = Protocol.receive(
                    self.sock
                )

                if message is None:
                    break

                self.handle_message(
                    message
                )

        except (
            ConnectionResetError,
            ConnectionAbortedError,
            BrokenPipeError,
            OSError
        ):

            pass

        finally:

            self.close()

            if self.on_disconnect:

                self.on_disconnect(
                    self
                )

    # =========================================================
    # MESSAGE HANDLING
    # =========================================================

    def handle_message(self, message):

        # -----------------------------------------------------
        # Username
        # -----------------------------------------------------

        if message.startswith("USERNAME:"):

            username = message[
                len("USERNAME:"):
            ]

            self.remote_username = username

            if self.on_username:

                self.on_username(
                    self,
                    username
                )

        # -----------------------------------------------------
        # Chat
        # -----------------------------------------------------

        elif message.startswith("CHAT:"):

            text = message[
                len("CHAT:"):
            ]

            if self.on_message:

                self.on_message(
                    self,
                    text
                )

        # -----------------------------------------------------
        # Typing
        # -----------------------------------------------------

        elif message == "TYPING":

            if self.on_typing:

                self.on_typing(
                    self
                )

        # -----------------------------------------------------
        # Stop typing
        # -----------------------------------------------------

        elif message == "STOP_TYPING":

            if self.on_stop_typing:

                self.on_stop_typing(
                    self
                )

    # =========================================================
    # SEND
    # =========================================================

    def send(self, message):

        if not self.running:
            return

        data = Protocol.encode(
            message
        )

        try:

            with self.send_lock:

                self.sock.sendall(
                    data
                )

        except (
            ConnectionResetError,
            ConnectionAbortedError,
            BrokenPipeError,
            OSError
        ):

            self.close()

    # =========================================================
    # CHAT
    # =========================================================

    def send_message(self, message):

        self.send(
            f"CHAT:{message}"
        )

    # =========================================================
    # TYPING
    # =========================================================

    def send_typing(self):

        self.send(
            "TYPING"
        )

    def send_stop_typing(self):

        self.send(
            "STOP_TYPING"
        )

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        if not self.running:
            return

        self.running = False

        try:

            self.sock.shutdown(
                socket.SHUT_RDWR
            )

        except OSError:
            pass

        try:

            self.sock.close()

        except OSError:
            pass


class Network:

    def __init__(self, username):

        self.username = username

        self.server = None

        self.running = False

        self.connections = {}

        self.lock = threading.Lock()

        # -----------------------------------------------------
        # Callbacks
        # -----------------------------------------------------

        self.on_connection = None
        self.on_message = None
        self.on_typing = None
        self.on_stop_typing = None
        self.on_disconnect = None
        self.on_error = None

    # =========================================================
    # SERVER
    # =========================================================

    def start_server(
        self,
        host="0.0.0.0",
        port=DEFAULT_PORT
    ):

        if self.running:
            return

        self.running = True

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
            f"TCP server listening on "
            f"{host}:{port}"
        )

        threading.Thread(
            target=self.accept_loop,
            daemon=True
        ).start()

    # =========================================================
    # ACCEPT CONNECTIONS
    # =========================================================

    def accept_loop(self):

        while self.running:

            try:

                sock, address = (
                    self.server.accept()
                )

                print(
                    f"Incoming connection from "
                    f"{address[0]}:{address[1]}"
                )

                self.create_connection(
                    sock,
                    address
                )

            except OSError:

                if self.running:
                    print(
                        "TCP server stopped."
                    )

                break

    # =========================================================
    # OUTGOING CONNECTION
    # =========================================================

    def connect(
        self,
        host,
        port=DEFAULT_PORT
    ):

        threading.Thread(
            target=self._connect,
            args=(host, port),
            daemon=True
        ).start()

    def _connect(
        self,
        host,
        port
    ):

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

            print(
                f"Connected to "
                f"{host}:{port}"
            )

            self.create_connection(
                sock,
                (host, port)
            )

        except socket.timeout:

            print(
                f"Connection to "
                f"{host}:{port} timed out."
            )

            sock.close()

            if self.on_error:

                self.on_error(
                    f"Connection to "
                    f"{host}:{port} timed out."
                )

        except ConnectionRefusedError:

            print(
                f"Connection refused by "
                f"{host}:{port}."
            )

            sock.close()

            if self.on_error:

                self.on_error(
                    f"Connection refused by "
                    f"{host}:{port}."
                )

        except OSError as e:

            print(
                f"Connection failed: {e}"
            )

            sock.close()

            if self.on_error:

                self.on_error(
                    str(e)
                )

    # =========================================================
    # CREATE CONNECTION
    # =========================================================

    def create_connection(
        self,
        sock,
        address
    ):

        connection = Connection(
            sock,
            address,
            self.username
        )

        # -----------------------------------------------------
        # Connection callbacks
        # -----------------------------------------------------

        connection.on_username = (
            self._handle_username
        )

        connection.on_message = (
            self._handle_message
        )

        connection.on_typing = (
            self._handle_typing
        )

        connection.on_stop_typing = (
            self._handle_stop_typing
        )

        connection.on_disconnect = (
            self._handle_disconnect
        )

        # -----------------------------------------------------
        # Send our username
        # -----------------------------------------------------

        connection.send(
            f"USERNAME:{self.username}"
        )

        connection.start()

    # =========================================================
    # USERNAME
    # =========================================================

    def _handle_username(
        self,
        connection,
        username
    ):

        connection.remote_username = username

        with self.lock:

            self.connections[username] = (
                connection
            )

        print(
            f"Connected to {username}"
        )

        if self.on_connection:

            self.on_connection(
                connection,
                username
            )

    # =========================================================
    # MESSAGE
    # =========================================================

    def _handle_message(
        self,
        connection,
        message
    ):

        if self.on_message:

            self.on_message(
                connection,
                message
            )

    # =========================================================
    # TYPING
    # =========================================================

    def _handle_typing(
        self,
        connection
    ):

        if self.on_typing:

            self.on_typing(
                connection
            )

    # =========================================================
    # STOP TYPING
    # =========================================================

    def _handle_stop_typing(
        self,
        connection
    ):

        if self.on_stop_typing:

            self.on_stop_typing(
                connection
            )

    # =========================================================
    # DISCONNECT
    # =========================================================

    def _handle_disconnect(
        self,
        connection
    ):

        username = (
            connection.remote_username
        )

        if username:

            with self.lock:

                existing = (
                    self.connections.get(
                        username
                    )
                )

                if existing is connection:

                    del self.connections[
                        username
                    ]

        if self.on_disconnect:

            self.on_disconnect(
                connection
            )

    # =========================================================
    # SEND TO CONTACT
    # =========================================================

    def send_message(
        self,
        username,
        message
    ):

        with self.lock:

            connection = (
                self.connections.get(
                    username
                )
            )

        if connection is None:

            print(
                f"No connection to "
                f"{username}"
            )

            return False

        connection.send_message(
            message
        )

        return True

    # =========================================================
    # TYPING TO CONTACT
    # =========================================================

    def send_typing(
        self,
        username
    ):

        with self.lock:

            connection = (
                self.connections.get(
                    username
                )
            )

        if connection:

            connection.send_typing()

    def send_stop_typing(
        self,
        username
    ):

        with self.lock:

            connection = (
                self.connections.get(
                    username
                )
            )

        if connection:

            connection.send_stop_typing()

    # =========================================================
    # CLOSE
    # =========================================================

    def stop(self):

        self.running = False

        if self.server:

            try:

                self.server.close()

            except OSError:
                pass

        with self.lock:

            connections = list(
                self.connections.values()
            )

            self.connections.clear()

        for connection in connections:

            connection.close()