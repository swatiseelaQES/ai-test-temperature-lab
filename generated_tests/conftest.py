import os

import requests
import urllib3


VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() not in {"0", "false", "no"}


if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    original_request = requests.sessions.Session.request

    def request_without_ssl_verification(self, method, url, **kwargs):
        kwargs.setdefault("verify", False)
        return original_request(self, method, url, **kwargs)

    requests.sessions.Session.request = request_without_ssl_verification