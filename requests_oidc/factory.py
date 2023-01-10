import webbrowser
from typing import Callable

import requests_oauthlib

from .catcher import RedirectCatcher
from .discovery import ServerDetails

TokenUpdater = Callable[[dict], None]


def make_oidc_session(
    oidc_url: str,
    client_id: str,
    port: int,
    updater: TokenUpdater | None = None,
    **kwargs
) -> requests_oauthlib.OAuth2Session:
    # Docstring set below to leverage f-strings
    
    auth_server = ServerDetails.discover(oidc_url)
    redirect_catcher = RedirectCatcher(port)

    session = requests_oauthlib.OAuth2Session(
        redirect_uri=redirect_catcher.redirect_uri,
        auto_refresh_url=auth_server.token_url,
        auto_refresh_kwargs={"client_id": client_id},
        token_updater=updater or (lambda token: None),
        client_id=client_id,
        **kwargs,
    )

    auth_redirect_url, _ = session.authorization_url(auth_server.auth_url)
    webbrowser.open(auth_redirect_url)

    path = redirect_catcher.catch()

    # requests_oauthlib insists you must redirect to https. So I lied to it.
    reply = "https://thecakeisalie.test" + path
    token = session.fetch_token(auth_server.token_url, authorization_response=reply)

    if updater:
        updater(token)

    return session

make_oidc_session.__doc__ = (
    f''' Create an `OAuth2Session <https://requests-oauthlib.readthedocs.io/en/latest/api.html#oauth-2-0-session>`_
    via web redirect, w/ automatic token management.

    After it is created, this session will behave as a regular
    `requests.Session <https://requests.readthedocs.io/en/latest/user/advanced/#session-objects>`_
    object,
    that injects the access token as an ``Authorization`` header. Do **not** use that session
    to call APIs that aren't the one you authenticated for, as that **will** leak your access
    token to third parties.

    To use this function, you'll need a **public** client w/ a ``redirect_uri`` set to
    ``{RedirectCatcher.FORMAT}``. Pick a unique ``port`` per client. Sharing the same one
    across different tools *may* work, but it's a bad assumption to rely on.

    The ``(client_id, port)`` tuple can be treated as constants within your code,
    and distributed as part of tooling that is built using this module.

    :param oidc_url: Path to an openid-connect server's `.well-known/openid-configuration`.
    :param client_id: Public client ID. This **must** be a public client w/o a secret.
    :param port: Port on localhost to redirect to from the auth server.
      ``{RedirectCatcher.FORMAT}`` must be a permitted ``redirect_uri`` for your client
      or the auth server will refuse to service your auth request.
    :param updater: Optional callback function to invoke whenever a token is fetched.
      This includes the first token fetch, and all refetches thereafter.


    .. _O2S: 
    .. _S: https://requests-oauthlib.readthedocs.io/en/latest/api.html#oauth-2-0-session
    '''
)