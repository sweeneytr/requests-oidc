from dataclasses import dataclass
from typing import Self

import requests


@dataclass
class ServerDetails:
    oidc_url: str
    auth_url: str
    token_url: str

    @classmethod
    def discover(cls, oidc_url: str) -> Self:
        res = requests.get(oidc_url)
        res.raise_for_status()
        data = res.json()

        return cls(
            oidc_url=oidc_url,
            auth_url=data["authorization_endpoint"],
            token_url=data["token_endpoint"],
        )
