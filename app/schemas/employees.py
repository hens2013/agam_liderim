from typing import Optional

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    personal_id: int
    first_name: str
    last_name: str
    position: str


class EmployeeResponse(BaseModel):
    personal_id: int
    first_name: str
    last_name: str
    position: str

    class Config:
        orm_mode = True


class AttachEmployeeRequest(BaseModel):
    personal_id: int
    government_id: int
