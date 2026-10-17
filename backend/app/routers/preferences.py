from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.models.account import Account
from app.models.preference import Preference
from app.schemas.preference import PreferenceOut, PreferenceUpdate

router = APIRouter(prefix="/student/preferences", tags=["student preferences"])


def _out(preference: Preference | None) -> PreferenceOut:
    if preference is None:
        return PreferenceOut()
    return PreferenceOut.model_validate(preference, from_attributes=True)


@router.get("", response_model=PreferenceOut)
def get_preferences(account: Account = Depends(require_student), db: Session = Depends(get_db)) -> PreferenceOut:
    return _out(db.get(Preference, account.id))


@router.put("", response_model=PreferenceOut)
def update_preferences(
    payload: PreferenceUpdate, account: Account = Depends(require_student), db: Session = Depends(get_db)
) -> PreferenceOut:
    preference = db.get(Preference, account.id)
    if preference is None:
        preference = Preference(student_id=account.id)
        db.add(preference)
    for field, value in payload.model_dump().items():
        setattr(preference, field, value)
    db.commit()
    db.refresh(preference)
    return _out(preference)
