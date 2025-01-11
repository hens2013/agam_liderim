from fastapi import APIRouter, HTTPException, Query, Depends, Request
from app.schemas.employers import EmployerCreate, EmployerResponse
from app.database.employers import create_employer_in_db, search_employers
from app.auth.jwt import decode_jwt, requires_auth

employers_router = APIRouter()


@employers_router.post("/", response_model=EmployerResponse)
@requires_auth
async def create_employer(request: Request, employer: EmployerCreate):
    try:
        new_employer = create_employer_in_db(employer)
        return new_employer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@employers_router.get("/get_employers", response_model=list[EmployerResponse])
@requires_auth
async def get_employers(request: Request,
                        search: str = None,
                        skip: int = 0,
                        limit: int = 10,
                        ):
    return search_employers(search=search, skip=skip, limit=limit)
