#!/usr/bin/env python
import datetime

from requests_oidc.factory import (make_client_credentials_session,
                                   make_os_cached_session)

session = make_os_cached_session(
    "testapp",
    "tsweeney",
    oidc_url="https://auth.nonprod.dustid.net/.well-known/openid-configuration",
    client_id="restish",
    port=8484,
)
print(session.token["id_token"])

session2 = make_client_credentials_session(
    oidc_url="https://auth.nonprod.dustid.net/.well-known/openid-configuration",
    client_id="keycloakify",
    client_secret=input("Keycloakify secret"),
)
print(session2.token)
