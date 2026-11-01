#It launches a PyQt5-based custom browser that uses Chromium configured to route all web 
# traffic through a Tor SOCKS5 proxy for enhanced privacy.



import os
import socket
import sys

from PyQt5.QtWidgets import QApplication

from tor import TOR_HOST, TOR_PORT
from main_window import GeekBrowserUI


def _tor_port_open(timeout: float = 0.5) -> bool:
    """
    QtWebEngine reads QTWEBENGINE_CHROMIUM_FLAGS once, before QApplication is
    created, and can't change its proxy config at runtime. So if we always
    hard-code the SOCKS5 proxy flag, every tab silently fails to load (blank/
    white page) whenever Tor hasn't been started yet -- which, on a fresh
    launch, is always. Only route through Tor if something is actually
    listening on the SOCKS port right now.
    """
    try:
        with socket.create_connection((TOR_HOST, TOR_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def _chromium_flags(use_tor: bool) -> str:
    flags = "--disable-gpu --disable-software-rasterizer"
    if use_tor:
        flags += f" --proxy-server=socks5://{TOR_HOST}:{TOR_PORT}"
        flags += " --proxy-bypass-list=localhost;127.*;10.*;172.16.*;192.168.*"
    return flags


if __name__ == "__main__":
    os.environ["QT_QUICK_BACKEND"] = "software"

    tor_already_running = _tor_port_open()
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _chromium_flags(tor_already_running)

    if tor_already_running:
        print(f"[SANAP] Tor detected on {TOR_HOST}:{TOR_PORT} -- routing all tabs through it.")
    else:
        print(
            f"[SANAP] Tor is not running on {TOR_HOST}:{TOR_PORT} yet -- "
            "starting with a direct connection. Start Tor from the ⬡ TOR panel, "
            "then RESTART the browser for tab traffic to route through it "
            "(QtWebEngine can't change its proxy after launch)."
        )

    print(f"[SANAP] Chromium flags: {os.environ['QTWEBENGINE_CHROMIUM_FLAGS']}")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GeekBrowserUI()
    window.show()

    sys.exit(app.exec_())