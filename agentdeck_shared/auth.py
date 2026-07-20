from fastapi import Header, HTTPException, status


def require_bearer_token(authorization: str | None, expected_token: str, label: str) -> None:
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{label} token is not configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")


def dashboard_auth(expected_token: str):
    def dependency(authorization: str | None = Header(default=None)) -> None:
        require_bearer_token(authorization, expected_token, "Dashboard")

    return dependency


def node_auth(expected_token: str):
    def dependency(authorization: str | None = Header(default=None)) -> None:
        require_bearer_token(authorization, expected_token, "Node")

    return dependency

