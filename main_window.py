from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTabWidget, QDialog, QMessageBox
)

from tor import TorManager, TOR_HOST, TOR_PORT
from tor_panel import TorPanel
from homepage import CustomHomepage
from browser_tab import IsolatedBrowserTab
from phishing import PhishingDetector
from widgets import StatusDot


class GeekBrowserUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SANAP Browser")
        self.setMinimumSize(1200, 750)

        self._tor = TorManager(self)
        self._tor.started.connect(self._on_tor_started)
        self._tor.stopped.connect(self._on_tor_stopped)
        self._tor.status_changed.connect(self._on_tor_status)
        self._tor.error.connect(self._on_tor_error)

        self._build_ui()

    # ── UI  ───────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #010a05; }
            QWidget {
                color: #00ff88;
                font-family: 'Courier New', monospace;
                background-color: #010a05;
            }
            QTabWidget::pane { border: 0; background: #010a05; }
            QTabWidget        { background: #010a05; }
            QTabBar           { background: #010a05; }
            QTabBar::tab {
                background: #010e06; color: #006633;
                font-family: 'Courier New', monospace;
                font-size: 13px; letter-spacing: 1px;
                padding: 6px 16px; margin-right: 2px;
                border-top:   1px solid #002211;
                border-left:  1px solid #002211;
                border-right: 1px solid #002211;
                border-bottom: none;
                border-top-left-radius:  4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #001a0d; color: #00ff88;
                border-top:   1px solid #00ff88;
                border-left:  1px solid #00ff88;
                border-right: 1px solid #00ff88;
            }
            QTabBar::tab:hover:!selected {
                color: #00cc66;
                border-top:   1px solid #00cc66;
                border-left:  1px solid #00cc66;
                border-right: 1px solid #00cc66;
            }
            QScrollBar:vertical          { background: #010a05; width: 6px; }
            QScrollBar::handle:vertical  { background: #00ff88; border-radius: 3px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        main = QWidget()
        main.setStyleSheet("background: #010a05;")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        ml.addWidget(self._build_top_bar())

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self._on_tab_switched)
        ml.addWidget(self.tabs, 1)

        ml.addWidget(self._build_status_bar())

        self.setCentralWidget(main)

        self.homepage = CustomHomepage(self)
        self.add_tab_widget(self.homepage, "HOME")

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(38)
        bar.setStyleSheet("QFrame { background: #000d06; border-bottom: 1px solid #001a0d; }")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        logo = QLabel("◈ SANAP")
        logo.setFixedWidth(72)
        logo.setStyleSheet("""
            QLabel {
                color: #00ff88; font-size: 13px; font-weight: 900;
                font-family: 'Courier New', monospace;
                background: transparent; letter-spacing: 2px;
            }
        """)

        self.back_btn    = self._nav_btn("◄", "Back")
        self.forward_btn = self._nav_btn("►", "Forward")
        self.reload_btn  = self._nav_btn("⟳", "Reload")
        self.new_tab_btn = self._nav_btn("+", "New Isolated Tab")

        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.reload_btn.clicked.connect(self.reload_page)
        self.new_tab_btn.clicked.connect(self.add_new_tab)

        url_container = QFrame()
        url_container.setStyleSheet("""
            QFrame { background: #000d06; border: 1px solid #002211; border-radius: 3px; }
            QFrame:focus-within { border: 1px solid #00ff88; }
        """)
        uh = QHBoxLayout(url_container)
        uh.setContentsMargins(8, 0, 8, 0)
        uh.setSpacing(6)

        self._shield_label = QLabel("🛡")
        self._shield_label.setFixedWidth(18)
        self._shield_label.setStyleSheet(
            "QLabel { background: transparent; font-size: 14px; border: none; }"
        )

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("enter url or search query...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none; color: #00ff88;
                font-size: 15px; font-family: 'Courier New', monospace;
                selection-background-color: #00ff88; selection-color: #000;
            }
        """)
        self.url_bar.returnPressed.connect(self.handle_url_bar)

        uh.addWidget(self._shield_label)
        uh.addWidget(self.url_bar)

        self._tor_btn = QPushButton("⬡ TOR: OFF")
        self._tor_btn.setFixedSize(110, 26)
        self._tor_btn.setCursor(Qt.PointingHandCursor)
        self._tor_btn.setToolTip("Open TOR routing panel")
        self._tor_btn.setStyleSheet(self._tor_btn_style(False))
        self._tor_btn.clicked.connect(self._open_tor_panel)

        self._newnym_btn = QPushButton("↺")
        self._newnym_btn.setFixedSize(26, 26)
        self._newnym_btn.setCursor(Qt.PointingHandCursor)
        self._newnym_btn.setToolTip("Request a new TOR circuit (new exit IP)")
        self._newnym_btn.setStyleSheet("""
            QPushButton {
                background: #0d0020; color: #3a0070;
                border: 1px solid #1a0040; border-radius: 3px; font-size: 15px;
            }
            QPushButton:hover   { color: #7000ff; border-color: #7000ff; }
            QPushButton:pressed { background: #7000ff; color: #fff; }
        """)
        self._newnym_btn.clicked.connect(self._quick_newnym)

        layout.addWidget(logo)
        layout.addSpacing(4)
        for b in (self.back_btn, self.forward_btn, self.reload_btn):
            layout.addWidget(b)
        layout.addSpacing(4)
        layout.addWidget(url_container, 1)
        layout.addSpacing(4)
        layout.addWidget(self.new_tab_btn)
        layout.addSpacing(6)
        layout.addWidget(self._tor_btn)
        layout.addWidget(self._newnym_btn)

        return bar

    def _build_status_bar(self):
        bar = QFrame()
        bar.setFixedHeight(22)
        bar.setStyleSheet("QFrame { background: #000d06; border-top: 1px solid #001a0d; }")
        sb = QHBoxLayout(bar)
        sb.setContentsMargins(12, 0, 12, 0)
        sb.setSpacing(16)

        self._status_label = QLabel("READY")
        self._status_label.setStyleSheet("""
            QLabel {
                color: #004422; font-size: 11px;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px; background: transparent;
            }
        """)

        self._shield_status = QLabel("PHISHING SHIELD: ACTIVE  |  TAB ISOLATION: ON")
        self._shield_status.setStyleSheet("""
            QLabel {
                color: #006633; font-size: 11px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px; background: transparent;
            }
        """)

        self._proxy_status_label = QLabel("PROXY: DIRECT")
        self._proxy_status_label.setStyleSheet("""
            QLabel {
                color: #003322; font-size: 10px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px; background: rgba(0,255,136,0.04);
                border: 1px solid #002211; padding: 1px 6px; border-radius: 2px;
            }
        """)

        self._isolation_badge = QLabel("⬡ ISOLATED")
        self._isolation_badge.setStyleSheet("""
            QLabel {
                color: #00ff88; font-size: 10px;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px; background: rgba(0,255,136,0.07);
                border: 1px solid #003322; padding: 1px 6px; border-radius: 2px;
            }
        """)

        sb.addWidget(StatusDot())
        sb.addWidget(self._status_label)
        sb.addStretch()
        sb.addWidget(self._shield_status)
        sb.addSpacing(6)
        sb.addWidget(self._proxy_status_label)
        sb.addSpacing(4)
        sb.addWidget(self._isolation_badge)

        return bar

    @staticmethod
    def _nav_btn(char, tip):
        b = QPushButton(char)
        b.setFixedSize(30, 26)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                background: #001a0d; color: #006633;
                border: 1px solid #002211; border-radius: 3px;
                font-size: 16px; font-family: 'Courier New', monospace;
            }
            QPushButton:hover   { background: #002a14; color: #00ff88; border: 1px solid #00ff88; }
            QPushButton:pressed { background: #00ff88; color: #000; }
        """)
        return b

    # ── TOR ───────────────────────────────────────────────────

    @staticmethod
    def _tor_btn_style(active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: rgba(112,0,255,0.12); color: #7000ff;
                    border: 1px solid #7000ff; border-radius: 3px;
                    font-size: 11px; font-family: 'Courier New', monospace;
                    letter-spacing: 1px;
                }
                QPushButton:hover   { background: rgba(112,0,255,0.22); }
                QPushButton:pressed { background: rgba(112,0,255,0.4);  }
            """
        return """
            QPushButton {
                background: #0d0020; color: #3a0070;
                border: 1px solid #1a0040; border-radius: 3px;
                font-size: 11px; font-family: 'Courier New', monospace;
                letter-spacing: 1px;
            }
            QPushButton:hover   { color: #7000ff; border-color: #7000ff; }
            QPushButton:pressed { color: #fff; }
        """

    def _sync_proxy_ui(self):
        running = self._tor.is_running
        self._tor_btn.setStyleSheet(self._tor_btn_style(running))
        self._tor_btn.setEnabled(True)
        self._newnym_btn.setEnabled(running)

        if running:
            self._tor_btn.setText("⬡ TOR: ON")
            self._proxy_status_label.setText(f"⛓ TOR  →  {TOR_HOST}:{TOR_PORT}")
            self._proxy_status_label.setStyleSheet("""
                QLabel {
                    color: #7000ff; font-size: 10px;
                    font-family: 'Courier New', monospace;
                    letter-spacing: 1px; background: rgba(112,0,255,0.07);
                    border: 1px solid #7000ff; padding: 1px 6px; border-radius: 2px;
                }
            """)
            self._shield_status.setText("TOR ROUTING: ACTIVE  |  TAB ISOLATION: ON")
        else:
            self._tor_btn.setText("⬡ TOR: OFF")
            self._proxy_status_label.setText("TOR: DIRECT")
            self._proxy_status_label.setStyleSheet("""
                QLabel {
                    color: #003322; font-size: 10px;
                    font-family: 'Courier New', monospace;
                    letter-spacing: 1px; background: rgba(0,255,136,0.04);
                    border: 1px solid #002211; padding: 1px 6px; border-radius: 2px;
                }
            """)
            self._shield_status.setText("PHISHING SHIELD: ACTIVE  |  TAB ISOLATION: ON")

    def _open_tor_panel(self):
        panel = TorPanel(self._tor, self)
        panel.exec_()
        self._sync_proxy_ui()

    def _quick_newnym(self):
        if not self._tor.is_running:
            QMessageBox.information(
                self, "TOR Not Running",
                "Start TOR first by clicking the ⬡ TOR button."
            )
            return
        self._tor.new_circuit()

    def _on_tor_started(self):
        self._sync_proxy_ui()
        proxy = QNetworkProxy(QNetworkProxy.Socks5Proxy, TOR_HOST, TOR_PORT)
        QNetworkProxy.setApplicationProxy(proxy)

    def _on_tor_stopped(self):
        self._sync_proxy_ui()
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.NoProxy))

    def _on_tor_status(self, msg: str):
        self._status_label.setText(msg)
        self._sync_proxy_ui()

    def _on_tor_error(self, msg: str):
        QMessageBox.critical(self, "TOR Error", msg)
        self._sync_proxy_ui()

    # ── tab  ────────────────────────────────────────────────

    def add_tab_widget(self, widget, title="NEW TAB"):
        idx = self.tabs.addTab(widget, title.upper())
        self.tabs.setCurrentIndex(idx)
        if isinstance(widget, IsolatedBrowserTab):
            self.tabs.setTabToolTip(
                idx,
                f"Isolated tab — profile: {widget.profile_name()}\n"
                "No cookies, cache, or storage shared with other tabs."
            )

    def add_new_tab(self):
        self.add_tab_widget(CustomHomepage(self), "HOME")

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            return
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if isinstance(widget, IsolatedBrowserTab):
            widget.setPage(QWebEnginePage())
            widget.deleteLater()

    def current_tab(self):
        return self.tabs.currentWidget()

    def _on_tab_switched(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, IsolatedBrowserTab):
            self.url_bar.setText(widget.url().toString())
            self._isolation_badge.setText(f"⬡ TAB {index + 1} ISOLATED")
        else:
            self.url_bar.clear()
            self._isolation_badge.setText("⬡ ISOLATED")

    # ── navigation ────────────────────────────────────────────────────

    def handle_url_bar(self):
        text = self.url_bar.text().strip()
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
        self.safe_open_url(url)

    def safe_open_url(self, url: str):
        self._status_label.setText("SCANNING URL...")
        self._shield_status.setText("ANALYZING THREAT LEVEL...")
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        detector  = PhishingDetector(url)
        risk      = detector.extract_features()
        breakdown = detector.get_score_breakdown()
        score     = sum(breakdown.values())

        if risk == 1:
            self._status_label.setText("SAFE — LOADING")
            self._shield_label.setText("🛡")
            self.load_url(url)
        elif risk == 0:
            self._status_label.setText("SUSPICIOUS URL DETECTED")
            self._show_warning(
                url, "SUSPICIOUS URL",
                "This URL shows suspicious patterns. Proceed with caution.",
                "#ffaa00", score, breakdown
            )
        else:
            self._status_label.setText("PHISHING URL BLOCKED")
            self._show_warning(
                url, "⚠ PHISHING URL DETECTED",
                "This URL is likely a phishing attempt. Proceed with extreme caution!",
                "#ff3333", score, breakdown
            )

    def load_url(self, url: str):
        tab   = self.current_tab()
        index = self.tabs.currentIndex()

        if isinstance(tab, IsolatedBrowserTab):
            tab.setUrl(QUrl(url))
            tab.urlChanged.connect(lambda u: self.url_bar.setText(u.toString()))
            self.tabs.setTabText(index, (url[:24] + "...") if len(url) > 24 else url)
        else:
            new_tab = IsolatedBrowserTab()
            new_tab.setUrl(QUrl(url))
            new_tab.urlChanged.connect(lambda u: self.url_bar.setText(u.toString()))
            new_tab.titleChanged.connect(self._update_tab_title)
            self.tabs.removeTab(index)
            label = (url[:24] + "...") if len(url) > 24 else url
            self.tabs.insertTab(index, new_tab, label.upper())
            self.tabs.setCurrentIndex(index)
            self.tabs.setTabToolTip(
                index,
                f"Isolated tab — profile: {new_tab.profile_name()}\n"
                "No cookies, cache, or storage shared with other tabs."
            )

        self.url_bar.setText(url)
        self._status_label.setText("LOADED")
        self._sync_proxy_ui()

    def _update_tab_title(self, title: str):
        idx = self.tabs.currentIndex()
        if title:
            label = (title[:20] + "...") if len(title) > 20 else title
            self.tabs.setTabText(idx, label.upper())

    def _show_warning(self, url, title, message, accent="#ff3333", score=0, breakdown=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(520, 380)
        dialog.setStyleSheet(f"""
            QDialog {{ background: #010a05; border: 1px solid {accent}; }}
            QLabel  {{ background: transparent; font-family: 'Courier New', monospace; }}
            QPushButton {{
                font-family: 'Courier New', monospace; font-size: 14px;
                font-weight: 900; letter-spacing: 2px;
                border-radius: 2px; padding: 8px 20px;
            }}
        """)
        vbox = QVBoxLayout(dialog)
        vbox.setContentsMargins(28, 24, 28, 24)
        vbox.setSpacing(12)

        icon_row = QHBoxLayout()
        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet(f"QLabel {{ color: {accent}; font-size: 40px; }}")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"QLabel {{ color: {accent}; font-size: 18px; font-weight: 900; letter-spacing: 3px; }}"
        )
        icon_row.addWidget(icon_lbl)
        icon_row.addSpacing(12)
        icon_row.addWidget(title_lbl)
        icon_row.addStretch()

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"QFrame {{ color: {accent}; background: {accent}; max-height: 1px; }}")

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("QLabel { color: #aaaaaa; font-size: 15px; }")

        url_display = QLabel(url[:70] + ("..." if len(url) > 70 else ""))
        url_display.setStyleSheet(f"""
            QLabel {{
                color: {accent}; font-size: 13px;
                background: rgba(255,0,0,0.05);
                border: 1px solid {accent}44;
                padding: 6px 10px; border-radius: 2px;
            }}
        """)

        if breakdown:
            score_lbl = QLabel(
                f"RISK SCORE: {score}  |  THRESHOLD: "
                f"{PhishingDetector.HIGH_THRESHOLD}=PHISHING  "
                f"{PhishingDetector.MED_THRESHOLD}=SUSPICIOUS"
            )
            score_lbl.setStyleSheet(
                f"QLabel {{ color: {accent}; font-size: 11px; letter-spacing: 1px; }}"
            )
            flags  = [f"[+{w}] {n}" for n, w in breakdown.items() if w > 0]
            goods  = [f"[{w}] {n}" for n, w in breakdown.items() if w < 0]
            detail = ""
            if flags: detail += "RISK: " + "  |  ".join(flags)
            if goods: detail += "  GOOD: " + "  |  ".join(goods)
            detail_lbl = QLabel(detail.strip() or "No specific signals flagged.")
            detail_lbl.setWordWrap(True)
            detail_lbl.setStyleSheet(
                "QLabel { color: #555555; font-size: 10px; letter-spacing: 1px; }"
            )

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("ABORT")
        cancel_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #666; border: 1px solid #333; }
            QPushButton:hover { color: #aaa; border-color: #555; }
        """)
        cancel_btn.clicked.connect(dialog.reject)

        proceed_btn = QPushButton("PROCEED ANYWAY")
        proceed_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {accent}; border: 1px solid {accent}; }}
            QPushButton:hover {{ background: {accent}22; }}
        """)
        proceed_btn.clicked.connect(dialog.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(proceed_btn)

        vbox.addLayout(icon_row)
        vbox.addWidget(div)
        vbox.addWidget(msg_lbl)
        vbox.addWidget(url_display)
        if breakdown:
            vbox.addWidget(score_lbl)
            vbox.addWidget(detail_lbl)
        vbox.addStretch()
        vbox.addLayout(btn_row)

        if dialog.exec_() != QDialog.Accepted:
            self._status_label.setText("NAVIGATION ABORTED")
            self._shield_status.setText("PHISHING SHIELD: ACTIVE  |  TAB ISOLATION: ON")
            return

        # second confirmation
        d2 = QDialog(self)
        d2.setWindowTitle("CONFIRM")
        d2.setFixedSize(380, 200)
        d2.setStyleSheet(f"""
            QDialog {{ background: #010a05; border: 1px solid {accent}; }}
            QLabel  {{ background: transparent; font-family: 'Courier New', monospace; }}
            QPushButton {{
                font-family: 'Courier New', monospace; font-size: 13px;
                font-weight: 900; letter-spacing: 2px;
                border-radius: 2px; padding: 7px 16px;
            }}
        """)
        v2 = QVBoxLayout(d2)
        v2.setContentsMargins(24, 20, 24, 20)
        v2.setSpacing(12)

        v2.addWidget(QLabel(
            "FINAL CONFIRMATION REQUIRED",
            styleSheet=f"color:{accent}; font-size:15px; font-weight:900; letter-spacing:2px;"
        ))
        sub = QLabel("Are you absolutely sure you want to navigate to this potentially dangerous URL?")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #888; font-size: 14px;")
        v2.addWidget(sub)
        v2.addStretch()

        br2 = QHBoxLayout()
        no_btn = QPushButton("NO, GO BACK")
        no_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#555;border:1px solid #333;}"
            "QPushButton:hover{color:#aaa;border-color:#555;}"
        )
        no_btn.clicked.connect(d2.reject)

        yes_btn = QPushButton("YES, LOAD IT")
        yes_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{accent};border:1px solid {accent};}}"
            f"QPushButton:hover{{background:{accent}22;}}"
        )
        yes_btn.clicked.connect(d2.accept)

        br2.addStretch()
        br2.addWidget(no_btn)
        br2.addWidget(yes_btn)
        v2.addLayout(br2)

        if d2.exec_() == QDialog.Accepted:
            self.load_url(url)
        else:
            self._status_label.setText("NAVIGATION ABORTED")
            self._shield_status.setText("PHISHING SHIELD: ACTIVE  |  TAB ISOLATION: ON")

    def go_back(self):
        t = self.current_tab()
        if isinstance(t, IsolatedBrowserTab):
            t.back()

    def go_forward(self):
        t = self.current_tab()
        if isinstance(t, IsolatedBrowserTab):
            t.forward()

    def reload_page(self):
        t = self.current_tab()
        if isinstance(t, IsolatedBrowserTab):
            t.reload()
