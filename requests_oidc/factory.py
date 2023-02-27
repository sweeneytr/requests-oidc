import json
import webbrowser
from pathlib import Path
from typing import Callable
import requests
import io
import time
import qrcode

from appdirs import AppDirs
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from requests_oauthlib import OAuth2Session

from .catcher import RedirectCatcher
from .discovery import ServerDetails

TokenUpdater = Callable[[dict], None]


def _make_scope(scope: list[str] | None) -> list[str]:
    if scope is None:
        return ["openid"]

    if "openid" in scope:
        return scope

    return ["openid"] + scope


def make_client_credentials_session(
    oidc_url: str,
    client_id: str,
    client_secret: str,
    updater: TokenUpdater | None = None,
    scope: list[str] | None = None,
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
        scope=_make_scope(scope),
        **kwargs,
    )

    def refresh_token(url, *args, **kwargs) -> dict:
        return session.fetch_token(
            url, client_id=client_id, client_secret=client_secret
        )

    session.refresh_token = refresh_token
    refresh_token(auth_server.token_url)

    return session


def make_oidc_session(
    oidc_url: str,
    client_id: str,
    port: int,
    token: dict | None = None,
    updater: TokenUpdater | None = None,
    scope: list[str] | None = None,
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
        scope=_make_scope(scope),
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

    if updater:
        updater(token)

    return session


def make_path_session(
    path: Path | str, *, klass=OAuth2Session, **kwargs
) -> OAuth2Session:
    """Same as ``make_oidc_session``, but saves/loads token to OS path."""
    match path:
        case str():
            path = Path(path)

    try:
        with path.open() as f:
            token = json.load(f)
    except FileNotFoundError:
        token = None

    def update(token: dict) -> None:
        with path.open("w") as f:
            json.dump(token, f)

    return make_oidc_session(token=token, updater=update, klass=klass, **kwargs)


def make_os_cached_session(
    appname: str,
    appauthor: str,
    filename: Path | str = "token.json",
    version: str | None = None,
    *,
    klass=OAuth2Session,
    **kwargs,
) -> OAuth2Session:
    """Same as ``make_oidc_session``, but saves/loads token to the OS-relevant user cache directory (appdata, ~/.cache/..., etc)."""
    appdirs = AppDirs(appname, appauthor, version)
    dir = Path(appdirs.user_cache_dir)
    dir.mkdir(parents=True, exist_ok=True)
    file = dir / filename
    return make_path_session(file, klass=klass, **kwargs)


def make_device_auth_session(
    oidc_url: str,
    client_id: str,
    audience: str,
    updater: TokenUpdater | None = None,
    scope: list[str] | None = None,
    *,
    klass=OAuth2Session,
    **kwargs,
):
    auth_server = ServerDetails.discover(oidc_url)

    res = requests.post(
        auth_server.device_url,
        data={
            "client_id": client_id,
            "scope": _make_scope(scope),
            "audience": audience,
        },
    )
    if not res.ok:
        print(res.json())
    res.raise_for_status()

    data = res.json()

    device_code = data["device_code"]
    expires_in = data["expires_in"]
    interval = data["interval"]
    print(f"Go to {data['verification_uri_complete']}")
    qr = qrcode.QRCode()
    qr.add_data(data["verification_uri_complete"])
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())

    start = time.time()
    while (time.time() - start) < expires_in:
        # Sleep at start so we don't hit the server like, 30ms after we begin the process
        time.sleep(interval)

        res = requests.post(
            auth_server.token_url,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id,
            },
        )

        if res.ok:
            break

        if res.status_code > 500:
            raise RuntimeError()

        try:
            data = res.json()
        except:
            res.raise_for_status()

        match data["error"]:
            case "authorization_pending":
                continue
            case "slow_down":
                # print a warning
                continue
            case "expired_token":
                raise RuntimeError("Device code flow timed out")
            case "invalid_grant":
                raise RuntimeError("Your code flow session is long dead, or invalid")
            case "access_denied":
                raise RuntimeError("Idiot")
        res.raise_for_status()

    res.raise_for_status()
    token = res.json()
    if token["expires_in"]:
        token["expires_at"] = time.time() + token["expires_in"]

    session = klass(
        auto_refresh_url=auth_server.token_url,
        auto_refresh_kwargs={"client_id": client_id},
        token=token,
        token_updater=updater or (lambda token: None),
        **kwargs,
    )

    if updater:
        updater(token)
        
    return session


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
