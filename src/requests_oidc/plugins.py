from pathlib import Path
import json
import appdirs
from typing import Optional


class PathPlugin:
    """Same as ``make_oidc_session``, but saves/loads token to OS path."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Optional[dict]:
        try:
            with self.path.open() as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def update(self, token: dict) -> None:
        with self.path.open("w") as f:
            json.dump(token, f)


class OSCachedPlugin(PathPlugin):
    """Same as ``make_oidc_session``, but saves/loads token to the OS-relevant user cache directory (appdata, ~/.cache/..., etc)."""

    def __init__(
        self,
        appname: str,
        appauthor: str,
        version: str | None = None,
        filename: str = "token.json",
    ) -> None:
        dirs = appdirs.AppDirs(appname=appname, appauthor=appauthor, version=version)
        dir = Path(dirs.user_cache_dir)
        dir.mkdir(parents=True, exist_ok=True)
        super().__init__(dir / filename)
