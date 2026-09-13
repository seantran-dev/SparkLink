# New-NetFirewallRule -DisplayName "SecureLink TCP 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
# New-NetFirewallRule -DisplayName "SecureLink UDP 5001" -Direction Inbound -Protocol UDP -LocalPort 5001 -Action Allow -Profile Private
import sys

from PySide6.QtWidgets import QApplication

from startup_gui import StartupGUI
from gui import GUI
from network import Network
from discovery import Discovery
from database import Database


app = QApplication(sys.argv)


database = Database()
identity = database.get_identity()


def start_securelink(username):

    user_id = database.create_identity(username)

    start_main_gui(
        username,
        user_id
    )


def start_main_gui(username, user_id):

    gui = GUI()

    network = Network(
        user_id,
        username
    )

    discovery = Discovery(
        user_id,
        username,
        5000
    )


    gui.network = network
    gui.discovery = discovery
    gui.database = database
    gui.user_id = user_id
    gui.load_contacts()

    network.on_connection = (
        lambda connection, remote_username:
            gui.signals.connection_received.emit(
                connection,
                remote_username
            )
    )

    network.on_message = (
        lambda connection, message:
            gui.signals.message_received.emit(
                connection,
                message
            )
    )

    network.on_typing = (
        lambda connection:
            gui.signals.typing_received.emit(
                connection
            )
    )

    network.on_stop_typing = (
        lambda connection:
            gui.signals.stop_typing_received.emit(
                connection
            )
    )

    network.on_disconnect = (
        lambda connection:
            gui.signals.connection_lost.emit(
                connection
            )
    )

    discovery.on_device_found = (
        lambda user_id, username, ip, port:
        gui.signals.device_found.emit(
            user_id,
            username,
            ip,
            port
        )
    )

    discovery.on_contact_found = (
        lambda user_id, username, ip, port:
            gui.handle_discovered_contact(
                user_id,
                username,
                ip,
                port
            )
    )
    
    discovery.on_device_lost = (
        lambda username, ip:
            gui.signals.device_lost.emit(
                username,
                ip
            )
    )

    network.on_file_received = (
        lambda connection, file_path, filename, file_size:
            gui.signals.file_received.emit(
                connection,
                file_path,
                filename,
                file_size
            )
    )

    network.start_server(
        "0.0.0.0",
        5000
    )

    discovery.start()

    gui.run()


if identity:

    username = identity["username"]
    user_id = identity["user_id"]

    print(
        f"Welcome back, {username}"
    )

    start_main_gui(
        username,
        user_id
    )

else:

    startup = StartupGUI()

    startup.set_continue_callback(
        start_securelink
    )

    startup.run()


sys.exit(
    app.exec()
)