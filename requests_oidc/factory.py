import webbrowser
from typing import Callable

import requests_oauthlib

from .catcher import RedirectCatcher
from .discovery import ServerDetails

TokenUpdater = Callable[[dict], None]


def make_oidc_session(
    oidc_url: str,
    client_id: str,
    redirect_port: int,
    updater: TokenUpdater | None = None,
    **kwargs
) -> requests_oauthlib.OAuth2Session:
    updater = updater or (lambda token: None)

    auth_server = ServerDetails.discover(oidc_url)
    redirect_catcher = RedirectCatcher(redirect_port)

    session = requests_oauthlib.OAuth2Session(
        redirect_uri=redirect_catcher.redirect_uri,
        auto_refresh_url=auth_server.token_url,
        auto_refresh_kwargs={"client_id": client_id},
        token_updater=lambda token: None,
        client_id=client_id,
        **kwargs,
    )

    auth_redirect_url, _ = session.authorization_url(auth_server.auth_url)
    webbrowser.open(auth_redirect_url)

    path = redirect_catcher.catch()

    # requests_oauthlib insists you must redirect to https. So I lied to it.
    reply = "https://thecakeisalie.test" + path
    session.fetch_token(auth_server.token_url, authorization_response=reply)

    return session
