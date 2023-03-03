#!/usr/bin/env python
import time

from requests_oidc.factory import (
    make_client_credentials_session,
    make_os_cached_session
)


def os():
    session = make_os_cached_session(
        "testapp",
        "tsweeney",
        oidc_url="https://auth.nonprod.dustid.net/.well-known/openid-configuration",
        client_id="restish",
        port=8484,
    )
    return session


def cc():
    session = make_client_credentials_session(
        oidc_url="https://auth.nonprod.dustid.net/.well-known/openid-configuration",
        client_id="restish",
        client_secret=input("restish secret"),
    )
    return session


session = os()

original_access_token = session.access_token

res = session.get("https://auth.nonprod.dustid.net/api/users")
res.raise_for_status()

# time.sleep(session.token["expires_in"] + 5)
# res = session.get("https://auth.nonprod.dustid.net/api/users")
# res.raise_for_status()

# new_access_token = session.access_token

# assert new_access_token != original_access_token

print('Test Complete')