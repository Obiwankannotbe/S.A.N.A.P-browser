import os
import sys
import shutil
import socket
import subprocess
import threading
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


TOR_HOST = "127.0.0.1"
TOR_PORT = 9050
TOR_CTRL = 9051


def _find_tor_executable() -> str:
    for name in ("tor", "tor.exe"):
        found = shutil.which(name)
        if found:
            return found

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for name in ("tor.exe", "tor"):
        p = os.path.join(script_dir, name)
        if os.path.isfile(p):
            return p
    for name in ("tor.exe", "tor"):
        p = os.path.join(script_dir, "tor", name)
        if os.path.isfile(p):
            return p

    win_bases = [r"C:\Program Files", r"C:\Program Files (x86)"]
    tor_sub        = os.path.join("Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe")
    tor_expert_sub = os.path.join("Tor Expert Bundle", "tor", "tor.exe")
    for base in win_bases:
        for sub in (tor_sub, tor_expert_sub):
            p = os.path.join(base, sub)
            if os.path.isfile(p):
                return p

    appdata_roots = []
    for env_var in ("LOCALAPPDATA", "APPDATA", "USERPROFILE"):
        v = os.environ.get(env_var, "")
        if v:
            appdata_roots.append(v)
    for root in appdata_roots:
        candidates = [
            os.path.join(root, "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(root, "Programs", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(root, "Microsoft", "WinGet", "Packages",
                         "TorProject.TorBrowser_Microsoft.Winget.Source_8wekyb3d8bbwe",
                         "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c

    for p in ("/usr/bin/tor", "/usr/local/bin/tor",
              "/opt/homebrew/bin/tor", "/opt/local/bin/tor", "/snap/bin/tor"):
        if os.path.isfile(p):
            return p

    return ""


class TorManager(QObject):
    started        = pyqtSignal()
    stopped        = pyqtSignal()
    status_changed = pyqtSignal(str)
    error          = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._running = False
        self._tor_exe = _find_tor_executable()
        self._lock    = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def executable(self) -> str:
        return self._tor_exe

    def start(self):
        if self._running:
            return
        if not self._tor_exe:
            self.error.emit(
                "TOR executable not found.\n\n"
                "Install options:\n"
                "  Windows: winget install TorProject.TorBrowser\n"
                "           or drop tor.exe next to sanap_browser.py\n"
                "  Linux  : sudo apt install tor\n"
                "  macOS  : brew install tor"
            )
            return
        self.status_changed.emit("TOR: STARTING...")
        t = threading.Thread(target=self._start_blocking, daemon=True)
        t.start()

    def stop(self):
        with self._lock:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None
            self._running = False
        self.stopped.emit()
        self.status_changed.emit("TOR: STOPPED")

    def new_circuit(self):
        if not self._running:
            self.error.emit("TOR is not running.")
            return
        t = threading.Thread(target=self._send_newnym, daemon=True)
        t.start()

    def _start_blocking(self):
        try:
            cmd = [
                self._tor_exe,
                "--SocksPort",            str(TOR_PORT),
                "--ControlPort",          str(TOR_CTRL),
                "--CookieAuthentication", "0",
                "--HashedControlPassword", "",
                "--Log",                  "notice stdout",
            ]
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
        except Exception as e:
            self.error.emit(f"Failed to start TOR: {e}")
            return

        for _ in range(60):
            if self._process.poll() is not None:
                self.error.emit("TOR process exited unexpectedly.")
                return
            if self._port_open(TOR_HOST, TOR_PORT):
                break
            time.sleep(0.5)
        else:
            self.error.emit("TOR did not open SOCKS port within 30 seconds.")
            self.stop()
            return

        with self._lock:
            self._running = True
        self.started.emit()
        self.status_changed.emit(f"TOR: ACTIVE  ●  {TOR_HOST}:{TOR_PORT}")

    def _send_newnym(self):
        try:
            with socket.create_connection((TOR_HOST, TOR_CTRL), timeout=5) as s:
                s.sendall(b"AUTHENTICATE\r\n")
                s.recv(256)
                s.sendall(b"SIGNAL NEWNYM\r\n")
                s.recv(256)
            self.status_changed.emit("TOR: NEW CIRCUIT ↺  —  NEW EXIT IP")
            QTimer.singleShot(2000, lambda: self.status_changed.emit(
                f"TOR: ACTIVE  ●  {TOR_HOST}:{TOR_PORT}"
            ))
        except Exception as e:
            self.error.emit(f"NEWNYM failed: {e}")

    @staticmethod
    def _port_open(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False
