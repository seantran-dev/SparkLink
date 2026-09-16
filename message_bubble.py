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
            QFont(family, 18)
        )

        # Bubble styling
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

        # Calculate the natural width of the text
        metrics = self.label.fontMetrics()
        text_width = metrics.horizontalAdvance(text)

        # Account for:
        # 12px left padding
        # 12px right padding
        # 1px left border
        # 1px right border
        bubble_width = text_width + 32

        # Maximum bubble width
        max_width = 500

        if bubble_width <= max_width:
            # Short message: no wrapping needed
            self.label.setWordWrap(False)
            self.label.setFixedWidth(bubble_width)
        else:
            # Long message: wrap inside maximum width
            self.label.setWordWrap(True)
            self.label.setFixedWidth(max_width)

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