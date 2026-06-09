"""Aceptación de invitaciones a un workspace (post-OAuth)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.security import WorkspaceContext, current_workspace, sign_jwt
from vigia_api.core.settings import Settings, get_settings
from vigia_api.services.audit import ACTION_INVITE_ACCEPTED, write_audit_event
from vigia_shared.models import AppUser, WorkspaceInvitation, WorkspaceMember

router = APIRouter(prefix="/invitations", tags=["invitations"])


class AcceptResponse(BaseModel):
    workspace_id: int
    role: str
    jwt: str


@router.post("/{token}/accept", response_model=AcceptResponse)
async def accept_invitation(
    token: str,
    request: Request,
    ctx: Annotated[WorkspaceContext, Depends(current_workspace)],
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> AcceptResponse:
    """El usuario logueado acepta una invitación: se agrega como miembro del workspace.

    Devuelve un JWT nuevo apuntando al workspace recién unido.
    """
    Session = get_sessionmaker()
    async with Session() as session:
        inv = await session.scalar(
            select(WorkspaceInvitation).where(WorkspaceInvitation.token == token)
        )
        if inv is None:
            raise HTTPException(404, "invitation_not_found")
        if inv.accepted_at is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "invitation_already_accepted")
        if inv.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_410_GONE, "invitation_expired")

        user = await session.get(AppUser, ctx.user_id)
        if user is None:
            raise HTTPException(404, "user_not_found")
        # (Opcional) validar que el email del invite coincide con el del user.
        if user.email.lower() != inv.email.lower():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "invitation_email_mismatch")

        existing = await session.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == inv.workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
        now = datetime.now(timezone.utc)
        if existing is None:
            member = WorkspaceMember(
                workspace_id=inv.workspace_id, user_id=user.id, role=inv.role, accepted_at=now
            )
            session.add(member)
            role = inv.role
        else:
            role = existing.role

        inv.accepted_at = now
        inv.accepted_by_user_id = user.id
        await write_audit_event(
            session, action=ACTION_INVITE_ACCEPTED, workspace_id=inv.workspace_id, user_id=user.id,
            resource=inv.email, request=request,
        )
        await session.commit()

        new_jwt = sign_jwt(user_id=user.id, workspace_id=inv.workspace_id, role=role, settings=settings)
        return AcceptResponse(workspace_id=inv.workspace_id, role=role, jwt=new_jwt)
