"""JWT signing/verification + dependencies FastAPI para multi-tenant.

- El web (NextAuth) firma un JWT con `{sub=user_id, ws=workspace_id, role}`
  tras Google OAuth + workspace upsert, usando el mismo `AUTH_SECRET` que la API.
- Cada request a endpoints protegidos pasa `Authorization: Bearer <jwt>`.
- `auth_enabled=False` deja la API en modo demo (sin gating).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.settings import Settings, get_settings
from vigia_shared.models import Workspace, WorkspaceMember
from sqlalchemy import select


@dataclass(frozen=True)
class WorkspaceContext:
    user_id: int
    workspace_id: int
    role: str
    plan: str

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"


def sign_jwt(*, user_id: int, workspace_id: int, role: str, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "ws": workspace_id,
        "role": role,
        "iat": now,
        "exp": now + s.auth_jwt_ttl_seconds,
    }
    return jwt.encode(payload, s.auth_secret, algorithm=s.auth_jwt_alg)


def verify_jwt(token: str, settings: Settings | None = None) -> dict:
    s = settings or get_settings()
    try:
        return jwt.decode(token, s.auth_secret, algorithms=[s.auth_jwt_alg])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid_token: {exc.__class__.__name__}",
        ) from exc


async def _load_workspace_context(user_id: int, workspace_id: int) -> WorkspaceContext:
    Session = get_sessionmaker()
    async with Session() as session:
        row = (
            await session.execute(
                select(Workspace, WorkspaceMember)
                .join(
                    WorkspaceMember,
                    (WorkspaceMember.workspace_id == Workspace.id)
                    & (WorkspaceMember.user_id == user_id),
                )
                .where(Workspace.id == workspace_id)
            )
        ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_a_member_of_workspace")
    ws, member = row
    return WorkspaceContext(user_id=user_id, workspace_id=ws.id, role=member.role, plan=ws.plan)


async def current_workspace(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> WorkspaceContext:
    """Dependency: 401 sin Bearer, 403 si no es miembro. En modo demo devuelve un contexto ficticio."""
    if not settings.auth_enabled:
        return WorkspaceContext(user_id=0, workspace_id=0, role="owner", plan="free")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_bearer_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_jwt(token, settings=settings)
    try:
        user_id = int(payload["sub"])
        workspace_id = int(payload["ws"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_token_claims") from exc
    return await _load_workspace_context(user_id, workspace_id)
