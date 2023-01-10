import urllib.parse as urlparser
from dataclasses import dataclass
from typing import Self

import requests

OIDC_PATH = ".well-known/openid-configuration"


@dataclass
class ServerDetails:
    oidc_url: str
    auth_url: str
    token_url: str

    @classmethod
    def discover(cls, oidc_url: str) -> Self:
        url = urlparser.urlparse(oidc_url)

        if not url.path.endswith(OIDC_PATH):
            url = url._replace(path=urlparser.urljoin(url.path, OIDC_PATH))

        oidc_url = urlparser.urlunparse(url)

        res = requests.get(oidc_url)
        res.raise_for_status()
        data = res.json()

        return cls(
            oidc_url=oidc_url,
            auth_url=data["authorization_endpoint"],
            token_url=data["token_endpoint"],
        )
