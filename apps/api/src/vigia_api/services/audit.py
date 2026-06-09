"""Audit log helpers. Escrituras best-effort: nunca rompen la operación de negocio."""
from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from vigia_shared.models import AuditLog

ACTION_LOGIN = "auth.login"
ACTION_INVITE_CREATED = "invite.created"
ACTION_INVITE_ACCEPTED = "invite.accepted"
ACTION_MEMBER_LEFT = "member.left"
ACTION_MEMBER_REMOVED = "member.removed"
ACTION_ONBOARDED = "workspace.onboarded"


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()[:64]
    return request.client.host[:64] if request.client else None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    return ua[:512] if ua else None


async def write_audit_event(
    session: AsyncSession,
    *,
    action: str,
    workspace_id: int | None = None,
    user_id: int | None = None,
    resource: str | None = None,
    params: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    try:
        await session.execute(
            insert(AuditLog).values(
                workspace_id=workspace_id,
                user_id=user_id,
                action=action,
                resource=resource,
                params=params,
                ip=_client_ip(request),
                user_agent=_user_agent(request),
            )
        )
    except Exception as exc:  # pragma: no cover
        print(f"[audit] write failed action={action} ws={workspace_id}: {exc!r}")
