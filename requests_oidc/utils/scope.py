def make_scope(scope: list[str] | None) -> list[str]:
    if scope is None:
        return ["openid"]

    if "openid" in scope:
        return scope

    return ["openid"] + scope
