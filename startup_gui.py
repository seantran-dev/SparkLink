import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)

from PySide6.QtCore import Qt

from PySide6.QtGui import (
    QFont,
    QFontDatabase,
)


class StartupGUI:

    def __init__(self):

        self.window = QWidget()

        self.window.setWindowTitle(
            "SecureLink"
        )

        self.window.resize(
            700,
            500
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
                18
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

        QLineEdit {
            background-color: #1A1A1A;
            border: 2px solid #2B2B2B;
            border-radius: 12px;
            padding: 12px;
            color: #F4F4F4;

            selection-background-color: #FFD24A;
            selection-color: #0B0B0B;
        }

        QLineEdit:focus {
            border: 2px solid #FFD24A;
        }

        QPushButton {
            background-color: #FFE680;
            border: 2px solid #FFE680;
            border-radius: 12px;
            padding: 12px 20px;
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

        """)

        # =====================================================
        # LAYOUT
        # =====================================================

        layout = QVBoxLayout()

        layout.setContentsMargins(
            180,
            80,
            180,
            80
        )

        layout.setSpacing(
            15
        )

        # =====================================================
        # TITLE
        # =====================================================

        title = QLabel(
            "SecureLink"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setFont(
            QFont(
                self.family,
                28,
                QFont.Weight.Normal
            )
        )

        title.setStyleSheet("""
            QLabel {
                color: #FFE680;
                padding-bottom: 5px;
            }
        """)

        layout.addWidget(
            title
        )

        # =====================================================
        # SUBTITLE
        # =====================================================

        subtitle = QLabel(
            "Secure Local Messaging"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setFont(
            QFont(
                self.family,
                15
            )
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #777777;
                padding-bottom: 30px;
            }
        """)

        layout.addWidget(
            subtitle
        )

        # =====================================================
        # USERNAME LABEL
        # =====================================================

        username_label = QLabel(
            "Username"
        )

        username_label.setFont(
            QFont(
                self.family,
                13
            )
        )

        username_label.setStyleSheet("""
            QLabel {
                color: #999999;
                padding-left: 4px;
            }
        """)

        layout.addWidget(
            username_label
        )

        # =====================================================
        # USERNAME INPUT
        # =====================================================

        self.username_box = QLineEdit()

        self.username_box.setPlaceholderText(
            "Enter your username"
        )

        self.username_box.setMaxLength(
            32
        )

        self.username_box.setMinimumHeight(
            48
        )

        layout.addWidget(
            self.username_box
        )

        # =====================================================
        # CONTINUE BUTTON
        # =====================================================

        self.continue_button = QPushButton(
            "Continue"
        )

        self.continue_button.setMinimumHeight(
            50
        )

        self.continue_button.setFont(
            QFont(
                self.family,
                15
            )
        )

        self.continue_button.clicked.connect(
            self.continue_clicked
        )

        self.username_box.returnPressed.connect(
            self.continue_clicked
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.continue_button
        )

        # =====================================================
        # STATUS
        # =====================================================

        self.status_label = QLabel(
            ""
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setFont(
            QFont(
                self.family,
                12
            )
        )

        self.status_label.setStyleSheet("""
            QLabel {
                color: #777777;
                padding-top: 8px;
            }
        """)

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

        self.window.setLayout(
            layout
        )

        # Callback assigned by main.py
        self.on_continue = None

    # =========================================================
    # USERNAME
    # =========================================================

    def get_username(self):

        return self.username_box.text().strip()

    # =========================================================
    # CONTINUE
    # =========================================================

    def continue_clicked(self):

        username = self.get_username()

        if not username:

            self.status_label.setText(
                "Please enter a username."
            )

            self.username_box.setFocus()

            return

        if self.on_continue:
            self.on_continue(username)

        self.window.close()

    # =========================================================
    # CALLBACK
    # =========================================================

    def set_continue_callback(
        self,
        callback
    ):

        self.on_continue = callback

    # =========================================================
    # SHOW
    # =========================================================

    def run(self):

        self.window.show()


# =============================================================
# STANDALONE TEST
# =============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    startup = StartupGUI()

    startup.set_continue_callback(
        lambda username:
            print(
                f"Username: {username}"
            )
    )

    startup.run()

    sys.exit(
        app.exec()
    )