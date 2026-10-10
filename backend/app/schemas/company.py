from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    company_name: str
    email: str
    location: str
