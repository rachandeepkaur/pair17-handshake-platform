import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_LABELS, permissions_for
from app.core.security import hash_password
from app.dependencies import CompanyContext
from app.models.account import Account
from app.models.company_member import CompanyMember, TeamInvitation
from app.schemas.team import (
    InvitationAccept,
    InvitationCreate,
    InvitationOut,
    InvitationPreview,
    InvitationWithToken,
    MemberOut,
    MembershipOut,
    PermissionInfo,
    PermissionMatrixOut,
    RoleInfo,
)

INVITATION_LIFETIME = timedelta(days=7)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def membership(ctx: CompanyContext) -> MembershipOut:
    return MembershipOut(
        member_id=ctx.member.id,
        name=ctx.member.name,
        email=ctx.account.email,
        role=ctx.role,
        role_label=ROLE_LABELS[ctx.role],
        permissions=permissions_for(ctx.role),
    )


def permission_matrix() -> PermissionMatrixOut:
    return PermissionMatrixOut(
        permissions=[PermissionInfo(key=key, label=label) for key, label in PERMISSIONS.items()],
        roles=[
            RoleInfo(
                key=role,
                label=label,
                description=ROLE_DESCRIPTIONS[role],
                permissions=permissions_for(role),
            )
            for role, label in ROLE_LABELS.items()
        ],
    )


# --- members ------------------------------------------------------------

def _member_out(member: CompanyMember, current_account_id: int) -> MemberOut:
    return MemberOut(
        id=member.id,
        account_id=member.account_id,
        name=member.name,
        email=member.account.email,
        role=member.role,
        role_label=ROLE_LABELS[member.role],
        last_active_at=member.last_active_at,
        created_at=member.created_at,
        is_you=member.account_id == current_account_id,
    )


def list_members(db: Session, ctx: CompanyContext) -> list[MemberOut]:
    rows = db.scalars(
        select(CompanyMember)
        .options(joinedload(CompanyMember.account))
        .where(CompanyMember.company_id == ctx.company_id)
        .order_by(CompanyMember.created_at, CompanyMember.id)
    ).all()
    # Owner first, then everyone else in join order.
    rows = sorted(rows, key=lambda member: member.role != "owner")
    return [_member_out(member, ctx.account.id) for member in rows]


def _get_manageable_member(db: Session, ctx: CompanyContext, member_id: int) -> CompanyMember:
    member = db.get(CompanyMember, member_id)
    if member is None or member.company_id != ctx.company_id:
        raise NotFoundError("Teammate not found")
    if member.role == "owner":
        raise ForbiddenError("The company owner can't be changed or removed")
    if member.account_id == ctx.account.id:
        raise ForbiddenError("You can't change or remove your own membership")
    return member


def update_member_role(db: Session, ctx: CompanyContext, member_id: int, role: str) -> MemberOut:
    member = _get_manageable_member(db, ctx, member_id)
    member.role = role
    db.commit()
    db.refresh(member)
    return _member_out(member, ctx.account.id)


def remove_member(db: Session, ctx: CompanyContext, member_id: int) -> None:
    member = _get_manageable_member(db, ctx, member_id)
    # A teammate's login exists only to act for this company, so removing
    # them deletes the account; the membership row cascades with it.
    db.delete(db.get(Account, member.account_id))
    db.commit()


def update_my_name(db: Session, ctx: CompanyContext, name: str) -> MembershipOut:
    ctx.member.name = name
    db.commit()
    db.refresh(ctx.member)
    return membership(ctx)


# --- invitations --------------------------------------------------------

def _invitation_out(invitation: TeamInvitation) -> InvitationOut:
    return InvitationOut(
        id=invitation.id,
        email=invitation.email,
        name=invitation.name,
        role=invitation.role,
        role_label=ROLE_LABELS[invitation.role],
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        expired=invitation.expires_at < datetime.now(),
    )


def _issue_token(invitation: TeamInvitation) -> str:
    token = secrets.token_urlsafe(32)
    invitation.token_hash = _hash_token(token)
    invitation.expires_at = datetime.now() + INVITATION_LIFETIME
    return token


def list_invitations(db: Session, ctx: CompanyContext) -> list[InvitationOut]:
    rows = db.scalars(
        select(TeamInvitation)
        .where(TeamInvitation.company_id == ctx.company_id)
        .order_by(TeamInvitation.created_at.desc())
    ).all()
    return [_invitation_out(row) for row in rows]


def create_invitation(db: Session, ctx: CompanyContext, payload: InvitationCreate) -> InvitationWithToken:
    if db.scalar(select(Account.id).where(Account.email == payload.email)):
        raise ConflictError("That email already has an account and can't be invited")
    if db.scalar(
        select(TeamInvitation.id).where(
            TeamInvitation.company_id == ctx.company_id, TeamInvitation.email == payload.email
        )
    ):
        raise ConflictError("That email already has a pending invitation. Regenerate its link instead.")

    invitation = TeamInvitation(
        company_id=ctx.company_id,
        email=payload.email,
        name=payload.name,
        role=payload.role,
        invited_by=ctx.account.id,
    )
    token = _issue_token(invitation)
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return InvitationWithToken(**_invitation_out(invitation).model_dump(), token=token)


def _get_company_invitation(db: Session, ctx: CompanyContext, invitation_id: int) -> TeamInvitation:
    invitation = db.get(TeamInvitation, invitation_id)
    if invitation is None or invitation.company_id != ctx.company_id:
        raise NotFoundError("Invitation not found")
    return invitation


def regenerate_invitation(db: Session, ctx: CompanyContext, invitation_id: int) -> InvitationWithToken:
    invitation = _get_company_invitation(db, ctx, invitation_id)
    token = _issue_token(invitation)
    db.commit()
    db.refresh(invitation)
    return InvitationWithToken(**_invitation_out(invitation).model_dump(), token=token)


def revoke_invitation(db: Session, ctx: CompanyContext, invitation_id: int) -> None:
    db.delete(_get_company_invitation(db, ctx, invitation_id))
    db.commit()


def _get_valid_invitation(db: Session, token: str) -> TeamInvitation:
    invitation = db.scalar(
        select(TeamInvitation)
        .options(joinedload(TeamInvitation.company))
        .where(TeamInvitation.token_hash == _hash_token(token))
    )
    if invitation is None:
        raise NotFoundError("This invitation link is invalid or has been revoked")
    if invitation.expires_at < datetime.now():
        raise BadRequestError("This invitation has expired. Ask your admin for a new link.")
    return invitation


def preview_invitation(db: Session, token: str) -> InvitationPreview:
    invitation = _get_valid_invitation(db, token)
    return InvitationPreview(
        company_name=invitation.company.company_name,
        email=invitation.email,
        name=invitation.name,
        role_label=ROLE_LABELS[invitation.role],
        expires_at=invitation.expires_at,
    )


def accept_invitation(db: Session, token: str, payload: InvitationAccept) -> Account:
    invitation = _get_valid_invitation(db, token)
    if db.scalar(select(Account.id).where(Account.email == invitation.email)):
        raise ConflictError("An account with this email already exists")

    account = Account(email=invitation.email, password_hash=hash_password(payload.password), role="company")
    db.add(account)
    db.flush()
    db.add(
        CompanyMember(
            company_id=invitation.company_id,
            account_id=account.id,
            name=payload.name,
            role=invitation.role,
            last_active_at=datetime.now(),
        )
    )
    db.delete(invitation)
    db.commit()
    db.refresh(account)
    return account
