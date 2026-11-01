from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEnginePage
)

_tab_counter = 0


class IsolatedBrowserTab(QWebEngineView):
    """
    Each tab spins up its own off-the-record QWebEngineProfile so cookies,
    cache, localStorage and IndexedDB are never shared between tabs, and
    nothing gets written to disk.
    """

    def __init__(self):
        super().__init__()
        global _tab_counter
        _tab_counter += 1

        self._profile = QWebEngineProfile(f"sanap_tab_{_tab_counter}", self)
        self._profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self._profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self._profile.clearAllVisitedLinks()
        self._profile.clearHttpCache()

        self._page = QWebEnginePage(self._profile, self)
        self.setPage(self._page)

        s = self._page.settings()
        s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows,        False)
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled,             False)
        s.setAttribute(QWebEngineSettings.PluginsEnabled,                  False)
        s.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled,        False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls,   False)

    def profile_name(self) -> str:
        return self._profile.storageName()
