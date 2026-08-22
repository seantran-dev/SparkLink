import socket
import threading
import time


DISCOVERY_PORT = 5001
DISCOVERY_MESSAGE = "SECURELINK"


class Discovery:

    def __init__(self, user_id, username, tcp_port=5000):
        self.user_id = user_id
        self.username = username
        self.tcp_port = tcp_port
        self.scanning = False
        self.running = False
        self.sock = None
        self.devices = {}
        self.on_device_found = None
        self.on_device_lost = None

    def start_scan(self):
        self.scanning = True
        print("Discovery scan started.")

    def stop_scan(self):
        self.scanning = False
        print("Discovery scan stopped.")

    def start(self):
        self.running = True

        threading.Thread(
            target=self.listen,
            daemon=True
        ).start()

        threading.Thread(
            target=self.broadcast,
            daemon=True
        ).start()

    def listen(self):

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.sock.bind(
            ("", DISCOVERY_PORT)
        )

        print(
            f"Discovery listening on UDP {DISCOVERY_PORT}"
        )

        while self.running:

            try:

                data, addr = self.sock.recvfrom(
                    1024
                )

                message = data.decode(
                    "utf-8"
                )

                parts = message.split("|")

                if len(parts) != 4:
                    continue

                identifier = parts[0]
                user_id = parts[1]
                username = parts[2]
                port = int(parts[3])

                if identifier != DISCOVERY_MESSAGE:
                    continue

                if user_id == self.user_id:
                    continue

                ip = addr[0]

                self.devices[user_id] = {
                    "user_id": user_id,
                    "username": username,
                    "ip": ip,
                    "port": port,
                    "last_seen": time.time()
                }

                if self.on_device_found:

                    self.on_device_found(
                        user_id,
                        username,
                        ip,
                        port
                    )

            except Exception as e:

                if self.running:
                    print(
                        f"Discovery error: {e}"
                    )

    def broadcast(self):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1
        )

        message = (
            f"{DISCOVERY_MESSAGE}|"
            f"{self.user_id}|"
            f"{self.username}|"
            f"{self.tcp_port}"
        )

        while self.running:

            if self.scanning:

                try:

                    sock.sendto(
                        message.encode("utf-8"),
                        (
                            "<broadcast>",
                            DISCOVERY_PORT
                        )
                    )

                except Exception as e:

                    print(
                        f"Broadcast error: {e}"
                    )

            time.sleep(2)