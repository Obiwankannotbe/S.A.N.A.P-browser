from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
)

from tor import TorManager, TOR_HOST, TOR_PORT


class TorPanel(QDialog):
    def __init__(self, tor: TorManager, parent=None):
        super().__init__(parent)
        self._tor = tor
        self.setWindowTitle("TOR ROUTING")
        self.setFixedSize(520, 380)
        self.setStyleSheet("""
            QDialog {
                background: #010a05;
                border: 1px solid #7000ff;
                font-family: 'Courier New', monospace;
            }
            QLabel      { background: transparent; color: #00ff88; }
            QPushButton {
                font-family: 'Courier New', monospace;
                font-size: 13px; font-weight: 900;
                letter-spacing: 2px; border-radius: 3px;
                padding: 8px 18px;
            }
        """)
        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(28, 24, 28, 24)
        vbox.setSpacing(14)

        title = QLabel("◈  TOR ROUTING ENGINE")
        title.setStyleSheet(
            "color: #7000ff; font-size: 17px; font-weight: 900; letter-spacing: 3px;"
        )

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("QFrame { color: #7000ff; background: #7000ff; max-height: 1px; }")

        self._status_lbl = QLabel("CHECKING...")
        self._status_lbl.setStyleSheet("font-size: 13px; letter-spacing: 2px; color: #444;")

        self._endpoint_lbl = QLabel(f"SOCKS5  →  {TOR_HOST}:{TOR_PORT}")
        self._endpoint_lbl.setStyleSheet("font-size: 11px; color: #003322; letter-spacing: 1px;")

        exe = self._tor.executable or "NOT FOUND"
        self._exe_lbl = QLabel(f"tor: {exe}")
        self._exe_lbl.setStyleSheet("font-size: 10px; color: #333;")
        self._exe_lbl.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._toggle_btn = QPushButton("START TOR")
        self._toggle_btn.setFixedHeight(36)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._on_toggle)

        self._newnym_btn = QPushButton("↺  NEW CIRCUIT")
        self._newnym_btn.setFixedHeight(36)
        self._newnym_btn.setCursor(Qt.PointingHandCursor)
        self._newnym_btn.setToolTip("Request a new TOR circuit (new exit IP)")
        self._newnym_btn.clicked.connect(self._on_newnym)

        btn_row.addWidget(self._toggle_btn)
        btn_row.addWidget(self._newnym_btn)

        self._hint_lbl = QLabel(
            "tor not found. Options:\n"
            "\n"
            "  [1] Easiest: drop tor.exe next to sanap_browser.py\n"
            "      (download Tor Expert Bundle from torproject.org)\n"
            "\n"
            "  [2] Install Tor Browser (then restart SANAP)\n"
            "      winget install TorProject.TorBrowser\n"
            "\n"
            "  [3] Linux: sudo apt install tor\n"
            "      macOS: brew install tor"
        )
        self._hint_lbl.setStyleSheet("color: #ffaa00; font-size: 11px;")
        self._hint_lbl.setWordWrap(True)

        vbox.addWidget(title)
        vbox.addWidget(div)
        vbox.addWidget(self._status_lbl)
        vbox.addWidget(self._endpoint_lbl)
        vbox.addWidget(self._exe_lbl)
        vbox.addStretch()
        vbox.addLayout(btn_row)
        vbox.addWidget(self._hint_lbl)

    def _connect_signals(self):
        self._tor.started.connect(self._refresh)
        self._tor.stopped.connect(self._refresh)
        self._tor.status_changed.connect(self._on_status)
        self._tor.error.connect(self._on_error)

    def _refresh(self):
        running = self._tor.is_running

        self._status_lbl.setText("● ACTIVE" if running else "○ STOPPED")
        self._status_lbl.setStyleSheet(
            f"font-size: 13px; letter-spacing: 2px; "
            f"color: {'#00ff88' if running else '#444'};"
        )
        self._endpoint_lbl.setStyleSheet(
            f"font-size: 11px; letter-spacing: 1px; "
            f"color: {'#00ff88' if running else '#003322'};"
        )
        self._toggle_btn.setText("STOP TOR" if running else "START TOR")

        if running:
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #ff3333;
                    border: 1px solid #ff3333; font-size: 11px; letter-spacing: 2px;
                }
                QPushButton:hover { background: rgba(255,50,50,0.1); }
            """)
        else:
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #00ff88;
                    border: 1px solid #00ff88; font-size: 11px; letter-spacing: 2px;
                }
                QPushButton:hover { background: rgba(0,255,136,0.1); }
            """)

        self._newnym_btn.setEnabled(running)
        self._newnym_btn.setStyleSheet(
            "background: transparent; color: #7000ff; border: 1px solid #7000ff;"
            if running else
            "background: transparent; color: #222; border: 1px solid #222;"
        )

        has_exe = bool(self._tor.executable)
        self._hint_lbl.setVisible(not has_exe)
        self._toggle_btn.setEnabled(has_exe)

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_error(self, msg: str):
        QMessageBox.critical(self, "TOR Error", msg)
        self._refresh()

    def _on_toggle(self):
        if self._tor.is_running:
            self._tor.stop()
        else:
            self._tor.start()

    def _on_newnym(self):
        self._tor.new_circuit()
