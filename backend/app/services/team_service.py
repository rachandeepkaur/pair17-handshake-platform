import hashlib
import secrets
from datetime import timedelta

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.activity import log_activity
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_LABELS, permissions_for
from app.core.security import hash_password
from app.dependencies import CompanyContext
from app.mongo import Doc, doc, docs, next_id, utcnow
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

def _emails(db: Database, account_ids: list[int]) -> dict[int, str]:
    return {row["_id"]: row["email"] for row in db.accounts.find({"_id": {"$in": account_ids}}, {"email": 1})}


def _member_out(member: Doc, email: str, current_account_id: int) -> MemberOut:
    return MemberOut(
        id=member.id,
        account_id=member.account_id,
        name=member.name,
        email=email,
        role=member.role,
        role_label=ROLE_LABELS[member.role],
        last_active_at=member.last_active_at,
        created_at=member.created_at,
        is_you=member.account_id == current_account_id,
    )


def list_members(db: Database, ctx: CompanyContext) -> list[MemberOut]:
    rows = docs(db.company_members.find({"company_id": ctx.company_id}).sort([("created_at", 1), ("_id", 1)]))
    emails = _emails(db, [row.account_id for row in rows])
    # Owner first, then everyone else in join order.
    rows = sorted(rows, key=lambda member: member.role != "owner")
    return [_member_out(member, emails.get(member.account_id, ""), ctx.account.id) for member in rows]


def _get_manageable_member(db: Database, ctx: CompanyContext, member_id: int) -> Doc:
    member = doc(db.company_members.find_one({"_id": member_id}))
    if member is None or member.company_id != ctx.company_id:
        raise NotFoundError("Teammate not found")
    if member.role == "owner":
        raise ForbiddenError("The company owner can't be changed or removed")
    if member.account_id == ctx.account.id:
        raise ForbiddenError("You can't change or remove your own membership")
    return member


def update_member_role(db: Database, ctx: CompanyContext, member_id: int, role: str) -> MemberOut:
    member = _get_manageable_member(db, ctx, member_id)
    db.company_members.update_one({"_id": member.id}, {"$set": {"role": role}})
    member["role"] = role
    log_activity(db, ctx.account.id, "team.role_changed", role="company", entity_type="member", entity_id=member.id,
                 details={"role": role})
    return _member_out(member, _emails(db, [member.account_id]).get(member.account_id, ""), ctx.account.id)


def remove_member(db: Database, ctx: CompanyContext, member_id: int) -> None:
    member = _get_manageable_member(db, ctx, member_id)
    # A teammate's login exists only to act for this company, so removing
    # them deletes the account, its membership, and any live sessions.
    db.company_members.delete_one({"_id": member.id})
    db.accounts.delete_one({"_id": member.account_id})
    db.sessions.delete_many({"account_id": member.account_id})
    db.messages.update_many({"sender_account_id": member.account_id}, {"$set": {"sender_account_id": None}})
    log_activity(db, ctx.account.id, "team.member_removed", role="company", entity_type="member", entity_id=member.id)


def update_my_name(db: Database, ctx: CompanyContext, name: str) -> MembershipOut:
    db.company_members.update_one({"_id": ctx.member.id}, {"$set": {"name": name}})
    ctx.member["name"] = name
    return membership(ctx)


# --- invitations --------------------------------------------------------

def _invitation_out(invitation: Doc) -> InvitationOut:
    return InvitationOut(
        id=invitation.id,
        email=invitation.email,
        name=invitation.name,
        role=invitation.role,
        role_label=ROLE_LABELS[invitation.role],
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        expired=invitation.expires_at < utcnow(),
    )


def _new_token() -> tuple[str, dict]:
    token = secrets.token_urlsafe(32)
    return token, {"token_hash": _hash_token(token), "expires_at": utcnow() + INVITATION_LIFETIME}


def list_invitations(db: Database, ctx: CompanyContext) -> list[InvitationOut]:
    rows = docs(db.team_invitations.find({"company_id": ctx.company_id}).sort([("created_at", -1)]))
    return [_invitation_out(row) for row in rows]


def create_invitation(db: Database, ctx: CompanyContext, payload: InvitationCreate) -> InvitationWithToken:
    if db.accounts.find_one({"email": payload.email}, {"_id": 1}):
        raise ConflictError("That email already has an account and can't be invited")
    if db.team_invitations.find_one({"company_id": ctx.company_id, "email": payload.email}, {"_id": 1}):
        raise ConflictError("That email already has a pending invitation. Regenerate its link instead.")

    token, token_fields = _new_token()
    invitation = {
        "_id": next_id(db, "team_invitations"),
        "company_id": ctx.company_id,
        "email": payload.email,
        "name": payload.name,
        "role": payload.role,
        "invited_by": ctx.account.id,
        **token_fields,
        "created_at": utcnow(),
    }
    db.team_invitations.insert_one(invitation)
    log_activity(db, ctx.account.id, "team.invited", role="company", entity_type="invitation", entity_id=invitation["_id"])
    return InvitationWithToken(**_invitation_out(Doc(invitation)).model_dump(), token=token)


def _get_company_invitation(db: Database, ctx: CompanyContext, invitation_id: int) -> Doc:
    invitation = doc(db.team_invitations.find_one({"_id": invitation_id}))
    if invitation is None or invitation.company_id != ctx.company_id:
        raise NotFoundError("Invitation not found")
    return invitation


def regenerate_invitation(db: Database, ctx: CompanyContext, invitation_id: int) -> InvitationWithToken:
    invitation = _get_company_invitation(db, ctx, invitation_id)
    token, token_fields = _new_token()
    db.team_invitations.update_one({"_id": invitation.id}, {"$set": token_fields})
    invitation.update(token_fields)
    return InvitationWithToken(**_invitation_out(invitation).model_dump(), token=token)


def revoke_invitation(db: Database, ctx: CompanyContext, invitation_id: int) -> None:
    invitation = _get_company_invitation(db, ctx, invitation_id)
    db.team_invitations.delete_one({"_id": invitation.id})


def _get_valid_invitation(db: Database, token: str) -> Doc:
    invitation = doc(db.team_invitations.find_one({"token_hash": _hash_token(token)}))
    if invitation is None:
        raise NotFoundError("This invitation link is invalid or has been revoked")
    if invitation.expires_at < utcnow():
        raise BadRequestError("This invitation has expired. Ask your admin for a new link.")
    return invitation


def preview_invitation(db: Database, token: str) -> InvitationPreview:
    invitation = _get_valid_invitation(db, token)
    company = db.companies.find_one({"_id": invitation.company_id}, {"company_name": 1}) or {}
    return InvitationPreview(
        company_name=company.get("company_name", ""),
        email=invitation.email,
        name=invitation.name,
        role_label=ROLE_LABELS[invitation.role],
        expires_at=invitation.expires_at,
    )


def accept_invitation(db: Database, token: str, payload: InvitationAccept) -> Doc:
    invitation = _get_valid_invitation(db, token)
    if db.accounts.find_one({"email": invitation.email}, {"_id": 1}):
        raise ConflictError("An account with this email already exists")

    now = utcnow()
    account = {
        "_id": next_id(db, "accounts"),
        "email": invitation.email,
        "password_hash": hash_password(payload.password),
        "role": "company",
        "created_at": now,
    }
    try:
        db.accounts.insert_one(account)
    except DuplicateKeyError as exc:
        raise ConflictError("An account with this email already exists") from exc
    db.company_members.insert_one(
        {
            "_id": next_id(db, "company_members"),
            "company_id": invitation.company_id,
            "account_id": account["_id"],
            "name": payload.name,
            "role": invitation.role,
            "last_active_at": now,
            "created_at": now,
        }
    )
    db.team_invitations.delete_one({"_id": invitation.id})
    log_activity(db, account["_id"], "team.invitation_accepted", role="company", entity_type="company",
                 entity_id=invitation.company_id)
    return Doc(account)
