import ipaddress
import re
import requests
import whois
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class PhishingDetector:
    HIGH_THRESHOLD = 4
    MED_THRESHOLD  = 2

    def __init__(self, url):
        self.url        = url
        self.domain     = ""
        self.ip_domain  = None
        self.response   = None
        self.soup       = None
        self.parsed     = None
        self.whois_data = None

        try:
            self.parsed = urlparse(url)
            self.domain = self.parsed.hostname or ""
        except Exception:
            pass

        try:
            self.ip_domain = ipaddress.ip_address(self.domain)
        except Exception:
            self.ip_domain = None

        if self.domain and self.ip_domain is None:
            try:
                # python-whois has no built-in timeout and can hang for a
                # long time on an unresponsive registrar, freezing the UI
                # since this whole class is constructed on the GUI thread.
                import socket as _socket
                _old_timeout = _socket.getdefaulttimeout()
                _socket.setdefaulttimeout(5)
                try:
                    self.whois_data = whois.whois(self.domain)
                finally:
                    _socket.setdefaulttimeout(_old_timeout)
            except Exception:
                self.whois_data = None

        try:
            headers       = {"User-Agent": "Mozilla/5.0"}
            self.response = requests.get(url, timeout=5, headers=headers, allow_redirects=True)
            self.soup     = BeautifulSoup(self.response.text, "html.parser")
        except Exception:
            self.response = None
            self.soup     = None

    def extract_features(self):
        score = sum(self.get_score_breakdown().values())
        if score >= self.HIGH_THRESHOLD:
            return -1
        if score >= self.MED_THRESHOLD:
            return 0
        return 1

    def get_score_breakdown(self):
        return {
            "IP Address as Domain":    self.check_ip_address(),
            "URL Length":              self.check_url_length(),
            "URL Shortener":           self.check_shortening_service(),
            "@ Symbol in URL":         self.check_at_symbol(),
            "Double-Slash Redirect":   self.check_double_slash_redirect(),
            "Prefix/Suffix (dash)":    self.check_prefix_suffix(),
            "Subdomain Depth":         self.check_subdomain_depth(),
            "HTTPS":                   self.check_https(),
            "Domain Age":              self.check_domain_age(),
            "Non-Standard Port":       self.check_non_standard_port(),
            "Redirect Chain":          self.check_redirect_chain(),
            "Suspicious Form Actions": self.check_form_actions(),
        }

    def check_ip_address(self):
        return 3 if self.ip_domain else 0

    def check_at_symbol(self):
        return 2 if "@" in self.url else 0

    def check_prefix_suffix(self):
        parts = self.domain.split(".")
        reg   = ".".join(parts[-2:]) if len(parts) >= 2 else self.domain
        return 1 if "-" in reg else 0

    def check_non_standard_port(self):
        port = self.parsed.port if self.parsed else None
        return 2 if port and port not in (80, 443) else 0

    def check_redirect_chain(self):
        return 1 if self.response and len(self.response.history) > 1 else 0

    def check_https(self):
        return -1 if self.parsed and self.parsed.scheme.lower() == "https" else 1

    def check_url_length(self):
        l = len(self.url)
        if l < 54:
            return 0
        if l <= 75:
            return 1
        return 2

    def check_shortening_service(self):
        pattern = (
            r"bit\.ly|goo\.gl|tinyurl\.com|ow\.ly|t\.co|is\.gd"
            r"|buff\.ly|adf\.ly|short\.link|rb\.gy|cutt\.ly|tiny\.cc"
        )
        return 2 if re.search(pattern, self.url, re.IGNORECASE) else 0

    def check_double_slash_redirect(self):
        after = re.sub(r"^https?://", "", self.url, count=1, flags=re.IGNORECASE)
        return 2 if "//" in after else 0

    def check_subdomain_depth(self):
        d = self.domain.count(".")
        if d <= 1:
            return 0
        if d == 2:
            return 1
        return 2

    def check_domain_age(self):
        if not self.whois_data:
            return 0
        try:
            c = self.whois_data.creation_date
            e = self.whois_data.expiration_date
            if isinstance(c, list): c = c[0]
            if isinstance(e, list): e = e[0]
            if c and e:
                age = (e.year - c.year) * 12 + (e.month - c.month)
                return -1 if age >= 12 else 2
        except Exception:
            pass
        return 0

    def check_form_actions(self):
        if not self.soup or not self.domain:
            return 0
        for form in self.soup.find_all("form"):
            action = form.get("action", "")
            if not action or action.lower().startswith("javascript"):
                return 2
            pa = urlparse(action)
            if pa.netloc and pa.netloc != self.domain:
                return 2
        return 0