from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies import CompanyContext, get_db, require_company, require_permission
from app.schemas.auth import TokenResponse
from app.schemas.team import (
    InvitationAccept,
    InvitationCreate,
    InvitationOut,
    InvitationPreview,
    InvitationWithToken,
    MemberOut,
    MemberRoleUpdate,
    MembershipOut,
    MyMemberUpdate,
    PermissionMatrixOut,
)
from app.services import team_service

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/me", response_model=MembershipOut, summary="Your own name, role, and permissions")
def get_me(ctx: CompanyContext = Depends(require_company)) -> MembershipOut:
    return team_service.membership(ctx)


@router.patch("/me", response_model=MembershipOut, summary="Update your display name")
def update_me(
    payload: MyMemberUpdate,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> MembershipOut:
    return team_service.update_my_name(db, ctx, payload.name)


@router.get("/permissions", response_model=PermissionMatrixOut, summary="Roles and what each can do")
def get_permissions(_: CompanyContext = Depends(require_company)) -> PermissionMatrixOut:
    return team_service.permission_matrix()


@router.get("/members", response_model=list[MemberOut], summary="List teammates")
def list_members(
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> list[MemberOut]:
    return team_service.list_members(db, ctx)


@router.patch("/members/{member_id}", response_model=MemberOut, summary="Change a teammate's role")
def update_member(
    member_id: int,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> MemberOut:
    return team_service.update_member_role(db, ctx, member_id, payload.role)


@router.delete("/members/{member_id}", status_code=204, summary="Remove a teammate (deletes their login)")
def remove_member(
    member_id: int,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> Response:
    team_service.remove_member(db, ctx, member_id)
    return Response(status_code=204)


@router.get("/invitations", response_model=list[InvitationOut], summary="List pending invitations")
def list_invitations(
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> list[InvitationOut]:
    return team_service.list_invitations(db, ctx)


@router.post(
    "/invitations",
    response_model=InvitationWithToken,
    status_code=201,
    summary="Invite a teammate; the response carries the one-time invite token",
)
def create_invitation(
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> InvitationWithToken:
    return team_service.create_invitation(db, ctx, payload)


@router.post(
    "/invitations/{invitation_id}/regenerate",
    response_model=InvitationWithToken,
    summary="Issue a new invite link (the old one stops working) and reset the expiry",
)
def regenerate_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> InvitationWithToken:
    return team_service.regenerate_invitation(db, ctx, invitation_id)


@router.delete("/invitations/{invitation_id}", status_code=204, summary="Revoke an invitation")
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("team:manage")),
) -> Response:
    team_service.revoke_invitation(db, ctx, invitation_id)
    return Response(status_code=204)


# --- public: the invitee isn't signed in yet ------------------------------

@router.get(
    "/invitations/token/{token}",
    response_model=InvitationPreview,
    summary="Preview an invitation from its link (no auth)",
)
def preview_invitation(token: str, db: Session = Depends(get_db)) -> InvitationPreview:
    return team_service.preview_invitation(db, token)


@router.post(
    "/invitations/token/{token}/accept",
    response_model=TokenResponse,
    summary="Accept an invitation: creates the login and signs in (no auth)",
)
def accept_invitation(token: str, payload: InvitationAccept, db: Session = Depends(get_db)) -> TokenResponse:
    account = team_service.accept_invitation(db, token, payload)
    return TokenResponse(
        access_token=create_access_token(subject=str(account.id), role=account.role),
        role=account.role,
    )
