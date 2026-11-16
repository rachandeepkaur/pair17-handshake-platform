from fastapi import APIRouter, Depends, Request, Response
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.activity import log_activity
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.core.sessions import create_session, revoke_other_sessions, revoke_session
from app.dependencies import get_current_user, get_db
from app.mongo import Doc, doc, next_id, utcnow
from app.schemas.auth import ChangePasswordRequest, CompanySignupRequest, LoginRequest, TokenResponse
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/auth", tags=["auth"])


def create_account(db: Database, email: str, password: str, role: str) -> Doc:
    """Insert an account with a bcrypt password hash; 409 if the email is taken."""

    if db.accounts.find_one({"email": email}, {"_id": 1}):
        raise ConflictError("An account with this email already exists")
    account = {
        "_id": next_id(db, "accounts"),
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": utcnow(),
    }
    try:
        db.accounts.insert_one(account)
    except DuplicateKeyError as exc:  # a concurrent signup won the race
        raise ConflictError("An account with this email already exists") from exc
    return Doc(account)


@router.post("/signup/company", response_model=CompanyOut, status_code=201)
def signup_company(payload: CompanySignupRequest, db: Database = Depends(get_db)) -> CompanyOut:
    account = create_account(db, payload.email, payload.password, "company")
    now = utcnow()
    db.companies.insert_one(
        {
            "_id": account.id,
            "account_id": account.id,
            "company_name": payload.company_name,
            "location": payload.location,
            "description": None,
            "contact_info": None,
            "profile_picture_path": None,
            "updated_at": now,
        }
    )
    # The signup account is the company's owner; the display name starts as
    # the company name and can be changed in Settings.
    db.company_members.insert_one(
        {
            "_id": next_id(db, "company_members"),
            "company_id": account.id,
            "account_id": account.id,
            "name": payload.company_name,
            "role": "owner",
            "last_active_at": None,
            "created_at": now,
        }
    )
    log_activity(db, account.id, "account.signup", role="company", entity_type="company", entity_id=account.id)
    return CompanyOut(
        account_id=account.id,
        company_name=payload.company_name,
        email=account.email,
        location=payload.location,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Database = Depends(get_db)) -> TokenResponse:
    # Single lookup against the shared accounts collection: works for a student
    # or a company account without the client having to say which it is.
    account = doc(db.accounts.find_one({"email": payload.email}))
    if account is None or not verify_password(payload.password, account.password_hash):
        log_activity(db, account.id if account else None, "auth.login_failed", details={"email": payload.email})
        raise UnauthorizedError("Invalid email or password")

    token = create_session(
        db,
        account,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    log_activity(db, account.id, "auth.login", role=account.role)
    return TokenResponse(access_token=token, role=account.role)


@router.post("/logout", status_code=204, summary="End the current session (the token stops working)")
def logout(db: Database = Depends(get_db), account: Doc = Depends(get_current_user)) -> Response:
    revoke_session(db, account.session)
    log_activity(db, account.id, "auth.logout", role=account.role)
    # The assistant's session memory ends with the login session.
    from app.assistant.memory import end_session

    end_session(db, account, account.session.id)
    return Response(status_code=204)


@router.post("/change-password", status_code=204, summary="Change the signed-in account's password")
def change_password(
    payload: ChangePasswordRequest,
    db: Database = Depends(get_db),
    account: Doc = Depends(get_current_user),
) -> Response:
    if not verify_password(payload.current_password, account.password_hash):
        # 400, not 401: the session is valid; only the confirmation failed.
        raise BadRequestError("Current password is incorrect")
    if verify_password(payload.new_password, account.password_hash):
        raise BadRequestError("New password must be different from the current one")

    db.accounts.update_one({"_id": account.id}, {"$set": {"password_hash": hash_password(payload.new_password)}})
    revoked = revoke_other_sessions(db, account.id, keep_session_id=account.session.id)
    log_activity(db, account.id, "auth.password_changed", role=account.role, details={"other_sessions_revoked": revoked})
    return Response(status_code=204)
