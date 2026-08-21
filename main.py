import sys

from PySide6.QtWidgets import QApplication

from startup_gui import StartupGUI
from gui import GUI
from network import Network
from discovery import Discovery


# =============================================================
# APPLICATION
# =============================================================

app = QApplication(sys.argv)


# =============================================================
# START SECURELINK
# =============================================================

def start_securelink(username):

    # ---------------------------------------------------------
    # Hide startup screen
    # ---------------------------------------------------------

    startup.window.hide()

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

    # ---------------------------------------------------------
    # Network → GUI
    #
    # Network runs on background threads, so we use Qt signals.
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
    # Start TCP server
    # ---------------------------------------------------------

    network.start_server(
        "0.0.0.0",
        5000
    )

    # ---------------------------------------------------------
    # Start LAN discovery
    # ---------------------------------------------------------

    discovery.start()

    # ---------------------------------------------------------
    # Show main GUI
    # ---------------------------------------------------------

    gui.run()


# =============================================================
# STARTUP SCREEN
# =============================================================

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