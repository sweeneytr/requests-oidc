import os

from .flows.auth_code import (
    make_oidc_session,
    make_os_cached_session,
    make_path_session,
)
from .flows.client_credentials import make_client_credentials_session
from .flows.device_code import make_device_code_session

# BS to work around oauthlib's wonkyness
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "True")
