
import socket
import threading
import time


DISCOVERY_PORT = 5001
DISCOVERY_INTERVAL = 2
DEVICE_TIMEOUT = 6

DISCOVERY_MESSAGE = "SECURELINK"


class Discovery:

    def __init__(
        self,
        username,
        tcp_port=5000
    ):

        self.username = username
        self.tcp_port = tcp_port

        self.running = False
        self.scanning = False

        self.listen_socket = None
        self.broadcast_socket = None

        self.devices = {}

        self.on_device_found = None
        self.on_device_lost = None

    # =========================================================
    # START
    # =========================================================

    def start(self):

        if self.running:
            return

        self.running = True

        threading.Thread(
            target=self.listen,
            daemon=True
        ).start()

        threading.Thread(
            target=self.broadcast,
            daemon=True
        ).start()

        threading.Thread(
            target=self.cleanup_devices,
            daemon=True
        ).start()

        print(
            "Discovery started."
        )

    # =========================================================
    # SCAN
    # =========================================================

    def start_scan(self):

        self.scanning = True

        print(
            "Discovery scan started."
        )

    def stop_scan(self):

        self.scanning = False

        print(
            "Discovery scan stopped."
        )

    # =========================================================
    # LISTEN
    # =========================================================

    def listen(self):

        self.listen_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.listen_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.listen_socket.bind(
            ("", DISCOVERY_PORT)
        )

        print(
            f"Discovery listening on "
            f"UDP {DISCOVERY_PORT}"
        )

        while self.running:

            try:

                data, address = (
                    self.listen_socket.recvfrom(
                        1024
                    )
                )

                message = data.decode(
                    "utf-8"
                )

                parts = message.split("|")

                if len(parts) != 3:
                    continue

                identifier = parts[0]
                username = parts[1]

                try:

                    port = int(
                        parts[2]
                    )

                except ValueError:

                    continue

                if identifier != DISCOVERY_MESSAGE:
                    continue

                # Ignore ourselves
                if username == self.username:
                    continue

                ip = address[0]

                self.devices[ip] = {
                    "username": username,
                    "ip": ip,
                    "port": port,
                    "last_seen": time.time()
                }

                print(
                    f"Discovered "
                    f"{username} "
                    f"at {ip}:{port}"
                )

                # Only report devices to the GUI
                # while the user is actively scanning.
                if (
                    self.scanning
                    and self.on_device_found
                ):

                    self.on_device_found(
                        username,
                        ip,
                        port
                    )

            except OSError as e:

                if self.running:

                    print(
                        f"Discovery socket error: {e}"
                    )

                break

            except Exception as e:

                if self.running:

                    print(
                        f"Discovery error: {e}"
                    )

    # =========================================================
    # BROADCAST
    # =========================================================

    def broadcast(self):

        self.broadcast_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.broadcast_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1
        )

        message = (
            f"{DISCOVERY_MESSAGE}|"
            f"{self.username}|"
            f"{self.tcp_port}"
        )

        while self.running:

            try:

                self.broadcast_socket.sendto(
                    message.encode("utf-8"),
                    (
                        "<broadcast>",
                        DISCOVERY_PORT
                    )
                )

            except OSError as e:

                if self.running:

                    print(
                        f"Discovery broadcast error: {e}"
                    )

                break

            except Exception as e:

                if self.running:

                    print(
                        f"Broadcast error: {e}"
                    )

            time.sleep(
                DISCOVERY_INTERVAL
            )

    # =========================================================
    # DEVICE TIMEOUT
    # =========================================================

    def cleanup_devices(self):

        while self.running:

            now = time.time()

            expired = []

            for ip, device in list(
                self.devices.items()
            ):

                if (
                    now - device["last_seen"]
                    > DEVICE_TIMEOUT
                ):

                    expired.append(ip)

            for ip in expired:

                device = self.devices.pop(
                    ip
                )

                if self.on_device_lost:

                    self.on_device_lost(
                        device["username"],
                        device["ip"]
                    )

            time.sleep(2)

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        self.running = False

        if self.listen_socket:

            try:

                self.listen_socket.close()

            except OSError:
                pass

        if self.broadcast_socket:

            try:

                self.broadcast_socket.close()

            except OSError:
                pass

        print(
            "Discovery stopped."
        )