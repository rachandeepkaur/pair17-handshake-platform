from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.core.activity import log_activity
from app.dependencies import get_db, require_student
from app.mongo import Doc as Account
from app.mongo import doc, encode, utcnow
from app.schemas.preference import PreferenceOut, PreferenceUpdate

router = APIRouter(prefix="/student/preferences", tags=["student preferences"])


def _out(preference) -> PreferenceOut:
    if preference is None:
        return PreferenceOut()
    return PreferenceOut.model_validate(preference, from_attributes=True)


@router.get("", response_model=PreferenceOut)
def get_preferences(account: Account = Depends(require_student), db: Database = Depends(get_db)) -> PreferenceOut:
    return _out(doc(db.preferences.find_one({"_id": account.id})))


@router.put("", response_model=PreferenceOut)
def update_preferences(
    payload: PreferenceUpdate, account: Account = Depends(require_student), db: Database = Depends(get_db)
) -> PreferenceOut:
    db.preferences.update_one(
        {"_id": account.id},
        {"$set": {**encode(payload.model_dump()), "student_id": account.id, "updated_at": utcnow()}},
        upsert=True,
    )
    log_activity(db, account.id, "preferences.updated", role="student")
    return _out(doc(db.preferences.find_one({"_id": account.id})))
