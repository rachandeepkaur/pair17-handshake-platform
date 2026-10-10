from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_db
from app.models.account import Account
from app.models.company import Company
from app.schemas.auth import CompanySignupRequest, LoginRequest, TokenResponse
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup/company", response_model=CompanyOut, status_code=201)
def signup_company(payload: CompanySignupRequest, db: Session = Depends(get_db)) -> CompanyOut:
    if db.query(Account).filter(Account.email == payload.email).first():
        raise ConflictError("An account with this email already exists")

    account = Account(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="company",
    )
    db.add(account)
    db.flush()  # assigns account.id before the company row references it

    company = Company(
        account_id=account.id,
        company_name=payload.company_name,
        location=payload.location,
    )
    db.add(company)
    db.commit()

    return CompanyOut(
        account_id=company.account_id,
        company_name=company.company_name,
        email=account.email,
        location=company.location,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # Single lookup against the shared accounts table: works for a student
    # or a company account without the client having to say which it is.
    account = db.query(Account).filter(Account.email == payload.email).first()
    if account is None or not verify_password(payload.password, account.password_hash):
        raise UnauthorizedError("Invalid email or password")

    token = create_access_token(account_id=account.id, role=account.role)
    return TokenResponse(access_token=token, role=account.role)
