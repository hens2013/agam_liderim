from pydantic import BaseModel


class EmployerCreate(BaseModel):
    employer_name: str
    government_id: int


class EmployerResponse(BaseModel):
    employer_name: str
    government_id: int

    class Config:
        orm_mode = True
