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
)

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    QTimer,
)

from PySide6.QtGui import (
    QFont,
    QFontDatabase,
)

from message_bubble import MessageBubble


class Signals(QObject):

    message_received = Signal(object, str)
    typing_received = Signal(object)
    stop_typing_received = Signal(object)

    connection_received = Signal(object, str)
    connection_lost = Signal(object)

    device_found = Signal(str, str, str, int)
    device_lost = Signal(str, str)


class ChatList(QListWidget):

    def wheelEvent(self, event):

        scroll_speed = 60

        delta = event.angleDelta().y()

        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value()
            - int(delta / 120 * scroll_speed)
        )


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
        }

        QListWidget::item:hover {
            background-color: #1A1A1A;
        }

        QListWidget::item:selected {
            background-color: #222222;
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

        contacts_label = QLabel(
            "CONTACTS"
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

        sidebar_layout.addWidget(
            contacts_label
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

        self.message_box.setEnabled(
            False
        )

        self.send_button.setEnabled(
            False
        )

        bottom.addWidget(
            self.message_box
        )

        bottom.addWidget(
            self.send_button
        )

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

                item.setText(
                    username
                )

                return

        item = QListWidgetItem(
            username
        )

        item.setData(
            Qt.ItemDataRole.UserRole,
            user_id
        )

        self.contacts_list.addItem(
            item
        )

    # =========================================================
    # SELECT CONTACT
    # =========================================================

    def select_contact(self, item):

        user_id = item.data(
            Qt.ItemDataRole.UserRole
        )
        
        print(
            "SELECT CONTACT:",
            user_id
        )

        print(
            "AVAILABLE CONNECTIONS:",
            list(self.network.connections.keys())
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

        self.hide_typing()

        connection = self.network.connections.get(
            user_id
        )

        if connection:
            self.message_box.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            self.message_box.setEnabled(False)
            self.send_button.setEnabled(False)

            self.network.connect(
                contact["ip"],
                int(contact["port"])
            )

    # =========================================================
    # LOAD CONVERSATION
    # =========================================================

    def load_conversation(self, user_id):

        self.chat.clear()

        messages = self.database.get_conversation(
            user_id
        )

        for message in messages:

            self.add_message_bubble(
                message["message_ciphertext"],
                message["sender_id"] == self.user_id
            )

        self.chat.scrollToBottom()

    # =========================================================
    # NEARBY DEVICES
    # =========================================================

    def add_nearby_device(self, user_id, username, ip, port):

        for i in range(
            self.nearby_list.count()
        ):

            item = self.nearby_list.item(i)

            device = item.data(
                Qt.ItemDataRole.UserRole
            )

            if device and device["ip"] == ip:

                device["user_id"] = user_id
                device["username"] = username
                device["port"] = int(port)

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    device
                )

                item.setText(
                    username
                )

                return

        item = QListWidgetItem(
            username
        )

        item.setData(
            Qt.ItemDataRole.UserRole,
            {
                "user_id": user_id,
                "username": username,
                "ip": ip,
                "port": int(port)
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
                port
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

        for i in range(
            self.nearby_list.count()
        ):

            item = self.nearby_list.item(i)

            device = item.data(
                Qt.ItemDataRole.UserRole
            )

            if device and device["user_id"] == user_id:

                self.nearby_list.takeItem(i)

                break

    # =========================================================
    # DISCONNECT
    # =========================================================

    def handle_disconnect(self, connection):

        if connection.user_id != self.current_contact:
            return

        self.message_box.setEnabled(
            False
        )

        self.send_button.setEnabled(
            False
        )

        self.typing_label.setText(
            "Disconnected"
        )

        self.typing_label.show()

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
            return

        self.hide_typing()

        self.add_message_bubble(
            message,
            False
        )
    
    def load_contacts(self):

        contacts = self.database.get_contacts()

        for contact in contacts:

            self.contacts[contact["user_id"]] = contact

            item = QListWidgetItem(
                contact["username"]
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                contact["user_id"]
            )

            self.contacts_list.addItem(
                item
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

        username = connection.username
        if username != self.current_contact:
            return

        self.typing_label.setText(
            f"{username} is typing..."
        )

        self.typing_label.show()

    # =========================================================
    # HIDE TYPING
    # =========================================================

    def hide_typing(self):

        self.typing_label.hide()

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