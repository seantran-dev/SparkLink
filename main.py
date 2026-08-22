import sys

from PySide6.QtWidgets import QApplication

from startup_gui import StartupGUI
from gui import GUI
from network import Network
from discovery import Discovery
from database import Database


app = QApplication(sys.argv)


# =============================================================
# DATABASE
# =============================================================

database = Database()

identity = database.get_identity()


# =============================================================
# START SECURELINK
# =============================================================

def start_securelink(username):

    # ---------------------------------------------------------
    # Create identity if this is the first launch
    # ---------------------------------------------------------

    user_id = database.create_identity(
        username
    )

    start_main_gui(
        username,
        user_id
    )


def start_main_gui(
    username,
    user_id
):

    # ---------------------------------------------------------
    # Create components
    # ---------------------------------------------------------

    gui = GUI()

    network = Network(
        username
    )

    discovery = Discovery(
        username,
        5000
    )

    # ---------------------------------------------------------
    # Connect components
    # ---------------------------------------------------------

    gui.network = network
    gui.discovery = discovery
    gui.database = database

    # ---------------------------------------------------------
    # Network → GUI
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Discovery → GUI
    # ---------------------------------------------------------

    discovery.on_device_found = (
        lambda username, ip, port:
            gui.signals.device_found.emit(
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

    # ---------------------------------------------------------
    # Start networking
    # ---------------------------------------------------------

    network.start_server(
        "0.0.0.0",
        5000
    )

    discovery.start()

    # ---------------------------------------------------------
    # Show GUI
    # ---------------------------------------------------------

    gui.run()


# =============================================================
# EXISTING IDENTITY
# =============================================================

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


# =============================================================
# FIRST LAUNCH
# =============================================================

else:

    startup = StartupGUI()

    startup.set_continue_callback(
        start_securelink
    )

    startup.run()


# =============================================================
# APPLICATION LOOP
# =============================================================

sys.exit(
    app.exec()
)