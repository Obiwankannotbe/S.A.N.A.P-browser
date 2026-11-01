from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)

from widgets import StatusDot


class CustomHomepage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._scan_pos = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._init_ui()

    def _tick(self):
        self._scan_pos = (self._scan_pos + 1) % max(1, self.height())
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0,   QColor("#010a05"))
        g.setColorAt(0.5, QColor("#000d08"))
        g.setColorAt(1,   QColor("#00050a"))
        p.fillRect(self.rect(), g)

        p.setPen(QPen(QColor(0, 255, 136, 12), 1))
        for x in range(0, self.width(),  40):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 40):
            p.drawLine(0, y, self.width(), y)

        sg = QLinearGradient(0, self._scan_pos - 60, 0, self._scan_pos + 20)
        sg.setColorAt(0,   QColor(0, 255, 136, 0))
        sg.setColorAt(0.8, QColor(0, 255, 136, 18))
        sg.setColorAt(1,   QColor(0, 255, 136, 0))
        p.fillRect(0, self._scan_pos - 60, self.width(), 80, sg)

        p.setPen(QPen(QColor("#00ff88"), 1))
        bsize, m = 24, 20
        corners = [
            (m, m),
            (self.width() - m, m),
            (m, self.height() - m),
            (self.width() - m, self.height() - m),
        ]
        for cx, cy in corners:
            dx = 1 if cx == m else -1
            dy = 1 if cy == m else -1
            p.drawLine(cx, cy, cx + dx * bsize, cy)
            p.drawLine(cx, cy, cx, cy + dy * bsize)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        center = QWidget()
        center.setAttribute(Qt.WA_TranslucentBackground)
        vbox = QVBoxLayout(center)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(0)

        logo = QLabel("◈")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "QLabel { color: #00ff88; font-size: 52px; background: transparent; }"
        )

        title = QLabel("SANAP Browser")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #00ff88; font-size: 42px; font-weight: 900;
                letter-spacing: 14px; font-family: 'Courier New', monospace;
                background: transparent;
            }
        """)

        sub = QLabel("Secure Anonymous Navigation And Privacy Browser")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("""
            QLabel {
                color: #006633; font-size: 11px; letter-spacing: 3px;
                font-family: 'Courier New', monospace; background: transparent;
            }
        """)

        vbox.addWidget(logo)
        vbox.addSpacing(6)
        vbox.addWidget(title)
        vbox.addSpacing(4)
        vbox.addWidget(sub)
        vbox.addSpacing(32)
        vbox.addWidget(self._build_search_bar(), alignment=Qt.AlignCenter)
        vbox.addSpacing(20)
        vbox.addLayout(self._build_status_row())

        layout.addWidget(center)

    def _build_search_bar(self):
        frame = QFrame()
        frame.setFixedWidth(560)
        frame.setStyleSheet("""
            QFrame {
                background: rgba(0,255,136,0.04);
                border: 1px solid #00ff88;
                border-radius: 4px;
            }
        """)
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 8, 8)
        row.setSpacing(8)

        prompt = QLabel("›_")
        prompt.setStyleSheet("""
            QLabel {
                color: #00ff88; font-size: 16px;
                font-family: 'Courier New', monospace;
                background: transparent; border: none;
            }
        """)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("enter url or search query...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none; color: #00ff88;
                font-size: 15px; font-family: 'Courier New', monospace;
                selection-background-color: #00ff88; selection-color: #000;
            }
        """)
        self.search_input.returnPressed.connect(self.handle_search)

        go_btn = QPushButton("ENTER")
        go_btn.setFixedSize(68, 30)
        go_btn.setCursor(Qt.PointingHandCursor)
        go_btn.setStyleSheet("""
            QPushButton {
                background: #00ff88; color: #000;
                font-family: 'Courier New', monospace; font-size: 11px;
                font-weight: 900; letter-spacing: 2px;
                border: none; border-radius: 2px;
            }
            QPushButton:hover   { background: #33ffaa; }
            QPushButton:pressed { background: #00cc66; }
        """)
        go_btn.clicked.connect(self.handle_search)

        row.addWidget(prompt)
        row.addWidget(self.search_input)
        row.addWidget(go_btn)
        return frame

    def _build_status_row(self):
        row = QHBoxLayout()
        row.setSpacing(20)
        row.setAlignment(Qt.AlignCenter)

        items = [
            ("PHISHING SHIELD", "ACTIVE"),
            ("TOR ROUTING",     "AVAILABLE"),
            ("TAB ISOLATION",   "ENABLED"),
        ]
        for label, val in items:
            item = QWidget()
            item.setAttribute(Qt.WA_TranslucentBackground)
            il = QHBoxLayout(item)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(6)

            dot = StatusDot()
            lbl = QLabel(f"{label}: <span style='color:#00ff88'>{val}</span>")
            lbl.setStyleSheet("""
                QLabel {
                    color: #006633; font-size: 10px;
                    font-family: 'Courier New', monospace;
                    background: transparent; letter-spacing: 1px;
                }
            """)
            il.addWidget(dot)
            il.addWidget(lbl)
            row.addWidget(item)

        return row

    def handle_search(self):
        text = self.search_input.text().strip()
        if not text:
            return
        if text.startswith("http://") or text.startswith("https://"):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            url = (
                f"https://duckduckgo.com/?q={text.replace(' ', '+')}"
                "&kae=d&k7=000000&k8=00ff88&k9=00ff88&kx=00ff88&kj=010a05&k21=010a05"
            )
        self.parent_window.safe_open_url(url)
