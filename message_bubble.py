from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy
)

from PySide6.QtCore import Qt

from PySide6.QtGui import (
    QFont,
    QFontDatabase
)


class MessageBubble(QWidget):

    def __init__(self, text, mine):
        super().__init__()

        font_id = QFontDatabase.addApplicationFont(
            "fonts/blender/BlenderPro-Medium.ttf"
        )

        family = QFontDatabase.applicationFontFamilies(
            font_id
        )[0]

        self.label = QLabel(text)

        self.label.setFont(
            QFont(
                family,
                18
            )
        )

        self.label.setWordWrap(True)

        text_width = (
            self.label
            .fontMetrics()
            .horizontalAdvance(text)
        )

        bubble_width = min(
            text_width + 36,
            500
        )

        self.label.setFixedWidth(
            bubble_width
        )

        self.label.adjustSize()



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