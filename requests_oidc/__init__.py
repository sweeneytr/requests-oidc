import os

from .factory import (
    make_client_credentials_session,
    make_oidc_session,
    make_os_cached_session,
    make_path_session,
)

# BS to work around oauthlib's wonkyness
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "True")