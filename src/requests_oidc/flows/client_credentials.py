from typing import List, Optional

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session  # type: ignore

from ..types import TokenUpdater
from ..utils import ServerDetails, make_scope


def make_client_credentials_session(
    oidc_url: str,
    client_id: str,
    client_secret: str,
    updater: Optional[TokenUpdater] = None,
    scope: Optional[List[str]] = None,
    *,
    klass=OAuth2Session,
    **kwargs,
) -> OAuth2Session:
    auth_server = ServerDetails.discover(oidc_url)
    client = BackendApplicationClient(client_id=client_id)
    session = klass(
        client=client,
        auto_refresh_url=auth_server.token_url,
        token_updater=updater or (lambda token: None),
        scope=make_scope(scope),
        **kwargs,
    )

    def refresh_token(url, *args, **kwargs) -> dict:
        return session.fetch_token(
            url, client_id=client_id, client_secret=client_secret
        )

    session.refresh_token = refresh_token
    refresh_token(auth_server.token_url)

    return session
