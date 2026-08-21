from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QHBoxLayout,
)

from PySide6.QtCore import (
    Qt,
)

from PySide6.QtGui import (
    QFont,
)


class MessageBubble(QWidget):

    def __init__(
        self,
        message,
        own_message,
        family="Arial"
    ):

        super().__init__()

        self.message = message
        self.own_message = own_message
        self.family = family

        # =====================================================
        # MESSAGE LABEL
        # =====================================================

        self.label = QLabel(
            message
        )

        self.label.setWordWrap(
            True
        )

        self.label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.label.setFont(
            QFont(
                family,
                14
            )
        )

        # =====================================================
        # BUBBLE STYLE
        # =====================================================

        if own_message:

            self.label.setStyleSheet("""
                QLabel {
                    background-color: #FFE680;
                    color: #0B0B0B;
                    border-radius: 12px;
                    padding: 10px 14px;
                }
            """)

        else:

            self.label.setStyleSheet("""
                QLabel {
                    background-color: #1A1A1A;
                    color: #F4F4F4;
                    border-radius: 12px;
                    padding: 10px 14px;
                }
            """)

        # =====================================================
        # LAYOUT
        # =====================================================

        layout = QHBoxLayout()

        layout.setContentsMargins(
            8,
            4,
            8,
            4
        )

        if own_message:

            layout.addStretch()

            layout.addWidget(
                self.label
            )

        else:

            layout.addWidget(
                self.label
            )

            layout.addStretch()

        self.setLayout(
            layout
        )

        # =====================================================
        # SIZE
        # =====================================================

        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy()
        )