from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QSizePolicy,
    QDialog,
    QFileDialog,
)

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    QTimer,
    QSize,
    QUrl,
    QEvent,
)

from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QDesktopServices,
)

from message_bubble import MessageBubble
from pathlib import Path

class Signals(QObject):

    message_received = Signal(object, str)
    typing_received = Signal(object)
    stop_typing_received = Signal(object)

    connection_received = Signal(object, str)
    connection_lost = Signal(object)

    device_found = Signal(str, str, str, int)
    device_lost = Signal(str, str)

    file_received = Signal(object, str, str, int)


class ChatList(QListWidget):

    def wheelEvent(self, event):

        scroll_speed = 60

        delta = event.angleDelta().y()

        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value()
            - int(delta / 120 * scroll_speed)
        )

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        if hasattr(
            self,
            "gui"
        ):

            self.gui.resize_chat_bubbles()



class ContactWidget(QWidget):

    def __init__(self, username, delete_callback, family):

        super().__init__()

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            False
        )

        self.setFixedHeight(
            40
        )

        layout = QHBoxLayout()

        layout.setContentsMargins(
            10,
            0,
            5,
            0
        )

        layout.setSpacing(5)

        self.name_label = QLabel(
            username
        )

        self.name_label.setFont(
            QFont(
                family,
                16
            )
        )

        self.name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #F4F4F4;
            }
        """)

        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.delete_button = QPushButton(
            "×"
        )

        self.delete_button.setFixedSize(
            24,
            28
        )

        self.delete_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #777777;
                font-size: 18px;
                padding: 0px;
            }

            QPushButton:hover {
                background: transparent;
                color: #FF5555;
            }

            QPushButton:pressed {
                background: transparent;
                color: #FF5555;
            }
        """)

        self.delete_button.clicked.connect(
            lambda: delete_callback()
        )

        layout.addWidget(
            self.name_label
        )

        layout.addWidget(
            self.delete_button
        )

        self.setLayout(
            layout
        )

class FileBubble(QWidget):
    def __init__(self, filename, file_path, mine):
        super().__init__()

        self.file_path = file_path

        font_id = QFontDatabase.addApplicationFont(
            "fonts/blender/BlenderPro-Medium.ttf"
        )
        family = QFontDatabase.applicationFontFamilies(font_id)[0]

        self.label = QLabel(f"<u>{filename}</u>")
        self.label.setFont(
            QFont(
                family,
                18
            )
        )
        self.label.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        text_width = (
            self.label
            .fontMetrics()
            .horizontalAdvance(f"{filename}")
        )

        bubble_width = min(
            text_width + 36,
            500
        )

        self.label.setFixedWidth(
            bubble_width
        )

        if mine:
            self.label.setStyleSheet("""
                QLabel {
                    background-color: rgba(20, 40, 35, 230);
                    color: #7dffb2;
                    border: 1px solid #00ff99;
                    border-radius: 3px;
                    padding: 8px 12px;
                }
            """)
        else:
            self.label.setStyleSheet("""
                QLabel {
                    background-color: rgba(10, 20, 25, 230);
                    color: #00D6E6;
                    border: 1px solid #00909E;
                    border-radius: 3px;
                    padding: 8px 12px;
                }
            """)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(
            10,
            5,
            10,
            5
        )
        layout.setSpacing(0)

        if mine:
            layout.addStretch()
            layout.addWidget(self.label)
        else:
            layout.addWidget(self.label)
            layout.addStretch()

        self.setLayout(layout)

        self.label.installEventFilter(self)

        def eventFilter(self, obj, event):
            if (
                obj == self.label
                and event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self.open_file()
                return True

            return super().eventFilter(obj, event)

        def open_file(self):
            path = Path(self.file_path).resolve()

            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(path))
            )

And your imports need:

class GUI:

    def __init__(self):

        # =====================================================
        # STATE
        # =====================================================

        self.network = None
        self.discovery = None
        self.database = None
        self.user_id = None

        self.current_contact = None

        # Contact information
        #
        # {
        #     "Bob": {
        #         "ip": "...",
        #         "port": 5000
        #     }
        # }
        self.contacts = {}
        self.unread_counts = {}

        # In-memory conversations for now.
        #
        # {
        #     "Bob": [
        #         ("them", "Hello"),
        #         ("me", "Hey")
        #     ]
        # }
        self.conversations = {}

        self.scanning = False

        self.is_typing = False

        # =====================================================
        # SIGNALS
        # =====================================================

        self.signals = Signals()

        self.signals.message_received.connect(
            self.display_friend_message
        )

        self.signals.typing_received.connect(
            self.show_typing
        )

        self.signals.stop_typing_received.connect(
            self.hide_typing
        )

        self.signals.connection_received.connect(
            self.handle_connection
        )

        self.signals.connection_lost.connect(
            self.handle_disconnect
        )

        self.signals.device_found.connect(
            self.add_nearby_device
        )

        self.signals.device_lost.connect(
            self.remove_nearby_device
        )

        self.signals.file_received.connect(
            self.display_friend_file
        )

        # =====================================================
        # WINDOW
        # =====================================================

        self.window = QWidget()

        self.window.setWindowTitle(
            "SecureLink"
        )

        self.window.resize(
            1000,
            650
        )

        self.window.setMinimumSize(
            1000,
            250
        )

        # =====================================================
        # FONT
        # =====================================================

        font_id = QFontDatabase.addApplicationFont(
            "fonts/blender/BlenderPro-Book.ttf"
        )

        if font_id != -1:

            families = (
                QFontDatabase
                .applicationFontFamilies(font_id)
            )

            if families:

                self.family = families[0]

            else:

                self.family = "Arial"

        else:

            self.family = "Arial"

        self.window.setFont(
            QFont(
                self.family,
                16
            )
        )

        # =====================================================
        # THEME
        # =====================================================

        self.window.setStyleSheet("""

        QWidget {
            background-color: #0B0B0B;
            color: #F4F4F4;
        }

        QListWidget {
            background-color: #111111;
            border: none;
            outline: none;
            padding: 10px;
        }

        QListWidget::item {
            border: none;
            padding: 0px;
            color: transparent;
        }


        QListWidget::item:hover {
            background-color: #1A1A1A;
            color: transparent;
        }

        QListWidget::item:selected {
            background-color: #222222;
            color: transparent;
        }

        QLineEdit {
            background-color: #1A1A1A;
            border: 2px solid #2B2B2B;
            border-radius: 12px;
            padding: 10px;
            color: white;

            selection-background-color: #FFD24A;
            selection-color: #0B0B0B;
        }

        QLineEdit:focus {
            border: 2px solid #3A3A3A;
        }

        QPushButton {
            background-color: #FFE680;
            border: 2px solid #FFE680;
            border-radius: 12px;
            padding: 10px 18px;
            color: #0B0B0B;
            font-weight: normal;
        }

        QPushButton:hover {
            background-color: #FFD24A;
            border: 2px solid #FFD24A;
        }

        QPushButton:pressed {
            background-color: #E6BD3F;
            border: 2px solid #E6BD3F;
        }

        QSplitter::handle {
            background-color: #222222;
        }

        """)

        # =====================================================
        # SIDEBAR
        # =====================================================

        sidebar = QWidget()

        sidebar.setMinimumWidth(
            220
        )

        sidebar.setMaximumWidth(
            320
        )

        sidebar_layout = QVBoxLayout()

        sidebar_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        sidebar_layout.setSpacing(
            8
        )

        # -----------------------------------------------------
        # Contacts title
        # -----------------------------------------------------

        contacts_header = QHBoxLayout()

        contacts_label = QLabel(
            "MESSAGES"
        )

        contacts_label.setFont(
            QFont(
                self.family,
                11,
                QFont.Weight.Bold
            )
        )

        contacts_label.setStyleSheet("""
            QLabel {
                color: #777777;
                padding-left: 5px;
                padding-bottom: 5px;
            }
        """)

        self.add_contact_button = QPushButton(
            "+"
        )

        self.add_contact_button.setFixedSize(
            24,
            24
        )

        self.add_contact_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #777777;
                font-size: 20px;
                padding: 0px;
                margin-top: -12px;
            }

            QPushButton:hover {
                background: transparent;
                color: #FFD24A;
            }

            QPushButton:pressed {
                background: transparent;
                color: #FFD24A;
            }
        """)

        self.add_contact_button.clicked.connect(
            self.show_contact_selector
        )

        contacts_header.addWidget(
            contacts_label
        )

        contacts_header.addStretch()

        contacts_header.addWidget(
            self.add_contact_button,
            alignment=Qt.AlignmentFlag.AlignVCenter
        )

        sidebar_layout.addLayout(
            contacts_header
        )

        # -----------------------------------------------------
        # Contacts list
        # -----------------------------------------------------

        self.contacts_list = QListWidget()

        

        self.contacts_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.contacts_list.itemClicked.connect(
            self.select_contact
        )

        sidebar_layout.addWidget(
            self.contacts_list
        )

        # -----------------------------------------------------
        # Scan button
        # -----------------------------------------------------


        # -----------------------------------------------------
        # Nearby title
        # -----------------------------------------------------

        nearby_label = QLabel(
            "NEARBY DEVICES"
        )

        nearby_label.setFont(
            QFont(
                self.family,
                11,
                QFont.Weight.Bold
            )
        )

        nearby_label.setStyleSheet("""
            QLabel {
                color: #777777;
                padding-left: 5px;
                padding-top: 10px;
                padding-bottom: 5px;
            }
        """)

        sidebar_layout.addWidget(
            nearby_label
        )

        # -----------------------------------------------------
        # Nearby list
        # -----------------------------------------------------

        self.nearby_list = QListWidget()

        self.nearby_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.nearby_list.itemClicked.connect(
            self.select_nearby
        )

        sidebar_layout.addWidget(
            self.nearby_list
        )

        self.scan_button = QPushButton(
            "Scan for Devices"
        )

        self.scan_button.clicked.connect(
            self.scan_devices
        )

        sidebar_layout.addWidget(
            self.scan_button
        )

        sidebar.setLayout(
            sidebar_layout
        )

        # =====================================================
        # CHAT AREA
        # =====================================================

        chat_widget = QWidget()

        chat_layout = QVBoxLayout()

        chat_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        # -----------------------------------------------------
        # Chat title
        # -----------------------------------------------------

        self.chat_title = QLabel(
            "Select a contact"
        )

        self.chat_title.setFont(
            QFont(
                self.family,
                20
            )
        )

        self.chat_title.setStyleSheet("""
            QLabel {
                color: #FFE680;
                padding-left: 5px;
                padding-bottom: 8px;
            }
        """)

        chat_layout.addWidget(
            self.chat_title
        )

        # -----------------------------------------------------
        # Chat messages
        # -----------------------------------------------------

        self.chat = ChatList()

        self.chat.gui = self

        self.chat.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.chat.setVerticalScrollMode(
            QListWidget.ScrollMode.ScrollPerPixel
        )

        self.chat.verticalScrollBar().setSingleStep(
            10
        )

        chat_layout.addWidget(
            self.chat
        )

        # -----------------------------------------------------
        # Typing indicator
        # -----------------------------------------------------

        self.typing_label = QLabel(
            ""
        )

        self.typing_label.hide()

        self.typing_label.setFont(
            QFont(
                self.family,
                12
            )
        )

        self.typing_label.setStyleSheet("""
            QLabel {
                color: #999999;
                padding-left: 12px;
            }
        """)

        chat_layout.addWidget(
            self.typing_label
        )

        # -----------------------------------------------------
        # Message input
        # -----------------------------------------------------

        bottom = QHBoxLayout()

        self.message_box = QLineEdit()

        self.message_box.setPlaceholderText(
            "Type a message..."
        )

        self.message_box.textEdited.connect(
            self.typing_changed
        )

        self.message_box.returnPressed.connect(
            self.send_message
        )

        self.send_button = QPushButton(
            "Send"
        )

        self.send_button.clicked.connect(
            self.send_message
        )

        self.file_button = QPushButton(
            "Image"
        )

        self.file_button.clicked.connect(
            self.send_image
        )

        self.message_box.setEnabled(False)
        self.send_button.setEnabled(False)
        self.file_button.setEnabled(False)

        bottom.addWidget(self.message_box)
        bottom.addWidget(self.send_button)
        bottom.addWidget(self.file_button)

        chat_layout.addLayout(
            bottom
        )

        chat_widget.setLayout(
            chat_layout
        )

        # =====================================================
        # MAIN SPLITTER
        # =====================================================

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        splitter.addWidget(
            sidebar
        )

        splitter.addWidget(
            chat_widget
        )

        splitter.setSizes(
            [250, 750]
        )

        layout = QHBoxLayout()

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.addWidget(
            splitter
        )

        self.window.setLayout(
            layout
        )

    # =========================================================
    # CONTACTS
    # =========================================================

    def add_contact(self, user_id, username, ip, port):

        self.contacts[user_id] = {
            "user_id": user_id,
            "username": username,
            "ip": ip,
            "port": int(port)
        }

        self.database.save_contact(
            user_id,
            username,
            ip,
            int(port)
        )

        for i in range(
            self.contacts_list.count()
        ):

            item = self.contacts_list.item(i)

            if item.data(
                Qt.ItemDataRole.UserRole
            ) == user_id:

                widget = self.contacts_list.itemWidget(
                    item
                )

                if widget:

                    widget.name_label.setText(
                        username
                    )

                return

        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            user_id
        )

        widget = ContactWidget(
            username,
            lambda: self.hide_conversation(user_id),
            self.family
        )

        self.contacts_list.addItem(
            item
        )

        self.contacts_list.setItemWidget(
            item,
            widget
        )

        item.setSizeHint(
            QSize(
                0,
                40
            )
        )

    def show_contact_selector(self):

        dialog = QDialog(
            self.window
        )

        dialog.setWindowTitle(
            "Select Contact"
        )

        dialog.setFixedSize(
            300,
            400
        )

        layout = QVBoxLayout()

        label = QLabel(
            "SELECT CONTACT"
        )

        label.setFont(
            QFont(
                self.family,
                12,
                QFont.Weight.Bold
            )
        )

        contacts_list = QListWidget()

        contacts_list.setStyleSheet("""
            QListWidget {
                background-color: #111111;
                border: none;
                outline: none;
                padding: 10px;
                color: #F4F4F4;
            }

            QListWidget::item {
                color: #F4F4F4;
                padding: 8px;
            }

            QListWidget::item:hover {
                background-color: #1A1A1A;
            }

            QListWidget::item:selected {
                background-color: #222222;
            }
        """)

        contacts = self.database.get_contacts()

        for contact in contacts:

            user_id = contact["user_id"]

            # Don't show contacts already visible
            visible = False

            for i in range(
                self.contacts_list.count()
            ):

                item = self.contacts_list.item(i)

                if item.data(
                    Qt.ItemDataRole.UserRole
                ) == user_id:

                    visible = True
                    break

            if visible:
                continue

            item = QListWidgetItem(
                contact["username"]
            )

            item.setFont(
                QFont(
                    self.family,
                    16
                )
            )


            item.setData(
                Qt.ItemDataRole.UserRole,
                user_id
            )

            contacts_list.addItem(
                item
            )

        layout.addWidget(
            label
        )

        layout.addWidget(
            contacts_list
        )

        dialog.setLayout(
            layout
        )

        def restore_contact(item):

            user_id = item.data(
                Qt.ItemDataRole.UserRole
            )

            contact = self.contacts.get(
                user_id
            )

            if not contact:
                contact = self.database.get_contact(
                    user_id
                )

            if not contact:
                return

            self.add_contact(
                contact["user_id"],
                contact["username"],
                contact["ip"],
                contact["port"]
            )

            dialog.accept()

        contacts_list.itemClicked.connect(
            restore_contact
        )

        dialog.exec()


    # =========================================================
    # SELECT CONTACT
    # =========================================================

    def select_contact(self, item):

        user_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        self.unread_counts[user_id] = 0

        self.update_contact_item(
            user_id
        )


        if not user_id:
            return

        contact = self.contacts.get(
            user_id
        )

        if not contact:
            return

        self.current_contact = user_id

        self.chat_title.setText(
            contact["username"]
        )

        self.load_conversation(
            user_id
        )

        connection = self.network.connections.get(
            user_id
        )

        if connection:

            self.message_box.setEnabled(True)
            self.send_button.setEnabled(True)
            self.file_button.setEnabled(True)

            self.typing_label.hide()

        else:

            self.message_box.setEnabled(False)
            self.send_button.setEnabled(False)
            self.file_button.setEnabled(False)
            
            self.typing_label.setText(
                "Offline"
            )

            self.typing_label.show()

            self.chat.scrollToBottom()

    # =========================================================
    # LOAD CONVERSATION
    # =========================================================

    def load_conversation(self, user_id):
        self.chat.clear()

        messages = self.database.get_conversation(
            user_id
        )

        for message in messages:
            mine = message["sender_id"] == self.user_id

            if message["message_type"] == "file":
                self.add_file_bubble(
                    message["message_ciphertext"],
                    message["message_nonce"],
                    mine
                )
            else:
                self.add_message_bubble(
                    message["message_ciphertext"],
                    mine
                )

        self.chat.scrollToBottom()

    # =========================================================
    # NEARBY DEVICES
    # =========================================================

    def add_nearby_device(
        self,
        user_id,
        username,
        ip,
        port
    ):

        if user_id == self.user_id:
            return

        port = int(port)

        if user_id in self.contacts:
            return

        if not self.scanning:
            return

        for i in range(
            self.nearby_list.count()
        ):

            item = self.nearby_list.item(i)

            device = item.data(
                Qt.ItemDataRole.UserRole
            )

            if device:

                if device["user_id"] == user_id:

                    device["username"] = username
                    device["ip"] = ip
                    device["port"] = port

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        device
                    )

                    item.setText(
                        username
                    )

                    return

        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            {
                "user_id": user_id,
                "username": username,
                "ip": ip,
                "port": port
            }
        )

        self.nearby_list.addItem(
            item
        )

    # =========================================================
    # REMOVE NEARBY DEVICE
    # =========================================================

    def remove_nearby_device(
        self,
        username,
        ip
    ):

        for i in range(
            self.nearby_list.count()
        ):

            item = self.nearby_list.item(i)

            device = item.data(
                Qt.ItemDataRole.UserRole
            )

            if device:

                if device["ip"] == ip:

                    self.nearby_list.takeItem(
                        i
                    )

                    return

    # =========================================================
    # SELECT NEARBY
    # =========================================================

    def select_nearby(self, item):

        device = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not device:
            return

        user_id = device["user_id"]
        username = device["username"]
        ip = device["ip"]
        port = int(device["port"])

        print(
            f"Connecting to "
            f"{username} "
            f"({ip}:{port})"
        )

        self.current_contact = user_id

        self.chat_title.setText(
            username
        )

        self.load_conversation(
            user_id
        )

        self.message_box.setEnabled(
            False
        )

        self.send_button.setEnabled(
            False
        )

        if self.network:
            self.network.connect(
                ip,
                port,
                user_id
            )

    # =========================================================
    # CONNECTION ESTABLISHED
    # =========================================================

    def handle_connection(self, connection, username):

        ip, port = connection.address

        user_id = connection.user_id

        self.add_contact(
            user_id,
            username,
            ip,
            port
        )

        if user_id == self.current_contact:

            self.message_box.setEnabled(True)
            self.send_button.setEnabled(True)
            self.file_button.setEnabled(True)

            self.hide_typing()

        for i in range(
            self.nearby_list.count()
        ):

            item = self.nearby_list.item(i)

            device = item.data(
                Qt.ItemDataRole.UserRole
            )

            if device and device["user_id"] == user_id:

                self.nearby_list.takeItem(
                    i
                )

                break

    def handle_discovered_contact(
        self,
        user_id,
        username,
        ip,
        port
    ):

        if user_id not in self.contacts:
            return

        if user_id in self.network.connections:
            return

        self.network.connect(
            ip,
            int(port),
            user_id
        )
    # =========================================================
    # DISCONNECT
    # =========================================================

    def handle_disconnect(self, connection):

        if connection.user_id != self.current_contact:
            return

        self.message_box.setEnabled(False)
        self.send_button.setEnabled(False)
        self.file_button.setEnabled(False)

        self.typing_label.setText(
            "Disconnected"
        )

        self.typing_label.show()

        self.chat.scrollToBottom()

    # =========================================================
    # SEND MESSAGE
    # =========================================================

    def send_message(self):

        if not self.current_contact:
            return

        message = (
            self.message_box
            .text()
            .strip()
        )

        if not message:
            return

        success = self.network.send(
            self.current_contact,
            message
        )

        if not success:
            return

        self.display_my_message(
            message
        )

        self.message_box.clear()

        if self.is_typing:

            self.stop_typing()

    def send_image(self):
        if not self.current_contact:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Select Image",
            "",
            "JPEG Images (*.jpg *.jpeg)"
        )

        if not file_path:
            return

        success = self.network.send_file(
            self.current_contact,
            file_path
        )

        if success:
            filename = Path(file_path).name

            self.database.save_message(
                conversation_id=self.current_contact,
                sender_id=self.user_id,
                message_ciphertext=filename,
                message_nonce=file_path
            )

            self.add_file_bubble(
                filename,
                file_path,
                True
            )


    # =========================================================
    # DISPLAY MY MESSAGE
    # =========================================================

    def display_my_message(self, message, save=True):

        if not self.current_contact:
            return

        if save:

            self.database.save_message(
                conversation_id=self.current_contact,
                sender_id=self.user_id,
                message_ciphertext=message
            )

        self.add_message_bubble(
            message,
            True
        )

    # =========================================================
    # DISPLAY FRIEND MESSAGE
    # =========================================================

    def display_friend_message(self, connection, message):

        user_id = connection.user_id
        username = connection.username

        if not user_id:
            return

        self.database.save_message(
            conversation_id=user_id,
            sender_id=user_id,
            message_ciphertext=message
        )

        if user_id != self.current_contact:

            self.show_hidden_conversation(
                user_id
            )

            self.unread_counts[user_id] = (
                self.unread_counts.get(
                    user_id,
                    0
                ) + 1
            )

            self.update_contact_item(
                user_id
            )

            return

        self.hide_typing()

        self.add_message_bubble(
            message,
            False
        )

    def display_friend_file(
        self,
        connection,
        file_path,
        filename,
        file_size
    ):
        user_id = connection.user_id

        if not user_id:
            return

        self.database.save_message(
            conversation_id=user_id,
            sender_id=user_id,
            message_ciphertext=filename,
            message_nonce=file_path,
            message_type="file"
        )

        if user_id != self.current_contact:
            self.show_hidden_conversation(user_id)

            self.unread_counts[user_id] = (
                self.unread_counts.get(
                    user_id,
                    0
                ) + 1
            )

            self.update_contact_item(
                user_id
            )

            return

        self.hide_typing()

        self.add_file_bubble(
            filename,
            file_path,
            False
        )

    def display_my_file(self, filename, file_path):
        bubble = FileBubble(
            filename,
            file_path,
            True,
        )

        item = QListWidgetItem()
        self.chat.addItem(item)
        self.chat.setItemWidget(item, bubble)
        item.setSizeHint(bubble.sizeHint())

        self.chat.scrollToBottom()

    def show_hidden_conversation(self, user_id):

        contact = self.contacts.get(user_id)

        if not contact:
            return

        # Check if already visible
        for i in range(
            self.contacts_list.count()
        ):

            item = self.contacts_list.item(i)

            if item.data(
                Qt.ItemDataRole.UserRole
            ) == user_id:
                return

        # Re-add the contact to the sidebar
        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            user_id
        )

        widget = ContactWidget(
            contact["username"],
            lambda: self.hide_conversation(user_id),
            self.family
        )

        self.contacts_list.addItem(
            item
        )

        self.contacts_list.setItemWidget(
            item,
            widget
        )

        item.setSizeHint(
            QSize(
                0,
                40
            )
        )

    def update_contact_item(self, user_id):

        count = self.unread_counts.get(
            user_id,
            0
        )

        for i in range(
            self.contacts_list.count()
        ):

            item = self.contacts_list.item(i)

            if item.data(
                Qt.ItemDataRole.UserRole
            ) != user_id:
                continue

            contact = self.contacts.get(
                user_id
            )

            if not contact:
                return

            username = contact["username"]

            if count > 0:

                item.setText(
                    f"{username}  ({count})"
                )

            else:

                item.setText(
                    username
                )

            return

    def load_contacts(self):

        contacts = self.database.get_contacts()

        for contact in contacts:

            user_id = contact["user_id"]

            self.contacts[user_id] = contact

            item = QListWidgetItem()

            item.setData(
                Qt.ItemDataRole.UserRole,
                user_id
            )

            item.setText("")

            widget = ContactWidget(
                contact["username"],
                lambda user_id=user_id:
                    self.hide_conversation(user_id),
                self.family
            )

            self.contacts_list.addItem(
                item
            )

            self.contacts_list.setItemWidget(
                item,
                widget
            )

            item.setSizeHint(
                QSize(
                    0,
                    40
                )
            )

    def hide_conversation(self, user_id):

        if user_id not in self.contacts:
            return

        # Hide the contact from the sidebar
        for i in range(
            self.contacts_list.count()
        ):

            item = self.contacts_list.item(i)

            if item.data(
                Qt.ItemDataRole.UserRole
            ) == user_id:

                self.contacts_list.takeItem(i)
                break

        # If this conversation is currently open,
        # close it
        if self.current_contact == user_id:

            self.current_contact = None

            self.chat.clear()

            self.chat_title.setText(
                "Select a contact"
            )

            self.message_box.setEnabled(False)
            self.send_button.setEnabled(False)
            self.file_button.setEnabled(False)

            self.hide_typing()

    def resize_chat_bubbles(self):

        width = self.chat.viewport().width()

        for i in range(
            self.chat.count()
        ):

            item = self.chat.item(i)

            bubble = self.chat.itemWidget(
                item
            )

            if bubble:

                bubble.setFixedWidth(
                    width
                )

                item.setSizeHint(
                    bubble.sizeHint()
                )
                
    def add_message_bubble(self, message, mine):

        bubble = MessageBubble(
            message,
            mine
        )

        item = QListWidgetItem()

        self.chat.addItem(item)

        self.chat.setItemWidget(
            item,
            bubble
        )

        bubble.setFixedWidth(
            self.chat.viewport().width()
        )

        item.setSizeHint(
            bubble.sizeHint()
        )

        self.chat.scrollToBottom()

    def add_file_bubble(self, filename, file_path, mine):
        file_path = str(Path(file_path).resolve())

        bubble = FileBubble(
            filename,
            file_path,
            mine
        )

        item = QListWidgetItem()

        self.chat.addItem(item)

        self.chat.setItemWidget(
            item,
            bubble
        )

        bubble.setFixedWidth(
            self.chat.viewport().width()
        )

        item.setSizeHint(
            bubble.sizeHint()
        )

        self.chat.scrollToBottom()
    # =========================================================
    # TYPING
    # =========================================================

    def typing_changed(self):

        if not self.current_contact:
            return

        if not self.is_typing:

            self.network.send_typing(
                self.current_contact
            )

            self.is_typing = True

        if not hasattr(
            self,
            "typing_timer"
        ):

            self.typing_timer = QTimer()

            self.typing_timer.setSingleShot(
                True
            )

            self.typing_timer.timeout.connect(
                self.stop_typing
            )

        self.typing_timer.start(
            2000
        )

    def stop_typing(self):

        if not self.is_typing:
            return

        if self.current_contact:

            self.network.send_stop_typing(
                self.current_contact
            )

        self.is_typing = False

    # =========================================================
    # SHOW TYPING
    # =========================================================

    def show_typing(
        self,
        connection
    ):

        user_id = connection.user_id
        username = connection.username

        if user_id != self.current_contact:
            return

        self.typing_label.setText(
            f"{username} is typing..."
        )

        self.typing_label.show()

        self.chat.scrollToBottom()

    # =========================================================
    # HIDE TYPING
    # =========================================================

    def hide_typing(self):

        self.typing_label.hide()

        self.chat.scrollToBottom()

    # =========================================================
    # SCAN
    # =========================================================

    def scan_devices(self):

        if not self.discovery:
            return

        self.nearby_list.clear()

        self.scanning = True

        self.scan_button.setText(
            "Scanning..."
        )

        self.scan_button.setEnabled(
            False
        )

        self.discovery.start_scan()

        QTimer.singleShot(
            5000,
            self.finish_scan
        )

    def finish_scan(self):

        self.scanning = False

        if self.discovery:

            self.discovery.stop_scan()

        self.scan_button.setText(
            "Scan Again"
        )

        self.scan_button.setEnabled(
            True
        )

    # =========================================================
    # RUN
    # =========================================================

    def run(self):

        self.window.show()