import json
import webbrowser
from pathlib import Path
from typing import List, Optional, Union

from appdirs import AppDirs
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from requests_oauthlib import OAuth2Session  # type: ignore

from ..types import TokenUpdater
from ..utils import RedirectCatcher, ServerDetails, make_scope


def make_oidc_session(
    oidc_url: str,
    client_id: str,
    port: int,
    token: Optional[dict] = None,
    updater: Optional[TokenUpdater] = None,
    scope: Optional[List[str]] = None,
    *,
    klass=OAuth2Session,
    **kwargs,
) -> OAuth2Session:
    # Docstring set below to leverage f-strings

    auth_server = ServerDetails.discover(oidc_url)
    redirect_catcher = RedirectCatcher(port)

    session = klass(
        redirect_uri=redirect_catcher.redirect_uri,
        auto_refresh_url=auth_server.token_url,
        auto_refresh_kwargs={"client_id": client_id},
        token=token,
        token_updater=updater or (lambda token: None),
        client_id=client_id,
        scope=make_scope(scope),
        **kwargs,
    )

    try:
        if token:
            token = session.refresh_token(auth_server.token_url)
    except OAuth2Error:
        token = None

    if not token:
        auth_redirect_url, _ = session.authorization_url(auth_server.auth_url)
        webbrowser.open(auth_redirect_url)

        path = redirect_catcher.catch()

        # requests_oauthlib insists you must use https. So I lied to it.
        reply = "https://thecakeisalie.test" + path
        token = session.fetch_token(auth_server.token_url, authorization_response=reply)

    if updater and token:
        updater(token)

    return session


def make_path_session(
    path: Union[Path, str],
    oidc_url: str,
    client_id: str,
    port: int,
    updater: Optional[TokenUpdater] = None,
    scope: Optional[List[str]] = None,
    *,
    klass=OAuth2Session,
    **kwargs,
) -> OAuth2Session:
    """Same as ``make_oidc_session``, but saves/loads token to OS path."""
    _path = Path(path)

    try:
        with _path.open() as f:
            token = json.load(f)
    except FileNotFoundError:
        token = None

    def update(token: dict) -> None:
        with _path.open("w") as f:
            json.dump(token, f)
        if updater:
            updater(token)

    return make_oidc_session(
        oidc_url=oidc_url,
        client_id=client_id,
        port=port,
        token=token,
        updater=update,
        scope=scope,
        klass=klass,
        **kwargs,
    )


def make_os_cached_session(
    oidc_url: str,
    client_id: str,
    port: int,
    appname: str,
    appauthor: str,
    filename: Union[Path, str] = "token.json",
    version: Optional[str] = None,
    updater: Optional[TokenUpdater] = None,
    scope: Optional[List[str]] = None,
    *,
    klass=OAuth2Session,
    **kwargs,
) -> OAuth2Session:
    """Same as ``make_oidc_session``, but saves/loads token to the OS-relevant user cache directory (appdata, ~/.cache/..., etc)."""
    appdirs = AppDirs(appname, appauthor, version)
    dir = Path(appdirs.user_cache_dir)
    dir.mkdir(parents=True, exist_ok=True)
    file = dir / filename
    return make_path_session(
        path=file,
        oidc_url=oidc_url,
        client_id=client_id,
        port=port,
        updater=updater,
        scope=scope,
        klass=klass,
        **kwargs,
    )


make_oidc_session.__doc__ = f""" Create an `OAuth2Session <https://requests-oauthlib.readthedocs.io/en/latest/api.html#oauth-2-0-session>`_
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
    """
