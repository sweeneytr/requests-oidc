import time


def access_expired(token: dict, margin: int = 0) -> bool:
    return (time.time()) > token["expires_at"] + margin


def refresh_expired(token: dict, margin: int = 0) -> bool:
    refresh_expires_at = (
        token["refresh_expires_in"] - token["expires_in"] + token["expires_at"]
    )
    return (time.time() + margin) > (refresh_expires_at + margin)
