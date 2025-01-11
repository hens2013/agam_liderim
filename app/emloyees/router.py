from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List, Dict, Union
from app.auth.jwt import requires_auth
from app.database.employers import get_employer_by_name
from app.schemas.employees import EmployeeCreate, EmployeeResponse, AttachEmployeeRequest
from app.database.employees import search_employees_in_db, create_employee_in_db, attach_employee_to_employer

employees_router = APIRouter()


@employees_router.get("/", response_model=List[EmployeeResponse])
@requires_auth
async def search_employees(
    request: Request,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> list[dict[str, int | str | None]]:
    """
    Search employees (requires authentication).
    Caches results for 1 minute.

    Args:
        request (Request): The HTTP request object.
        search (Optional[str]): Search query for employees.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to retrieve.

    Returns:
        List[EmployeeResponse]: List of employees matching the search criteria.
    """
    return search_employees_in_db(search=search, skip=skip, limit=limit)


@employees_router.post("/", response_model=EmployeeResponse)
@requires_auth
async def create_employee(
    request: Request,
    employee: EmployeeCreate
) -> dict[str, int | str]:
    """
    Create a new employee (requires authentication).

    Args:
        request (Request): The HTTP request object.
        employee (EmployeeCreate): The details of the employee to create.

    Returns:
        EmployeeResponse: The newly created employee's details.

    Raises:
        HTTPException: If there is an error during employee creation.
    """
    try:
        new_employee = create_employee_in_db(employee)
        return new_employee
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@employees_router.patch("/attach", response_model=Dict[str, Union[str, Dict]])
@requires_auth
async def attach_employee(request: Request, attach_data: AttachEmployeeRequest) -> Dict[str, Union[str, Dict]]:
    """
    Attach an employee to an employer by updating the employee's government_id.

    Args:
        request (AttachEmployeeRequest): The request containing the employee ID and employer details.

    Returns:
        Dict[str, Union[str, Dict]]: Confirmation message and the updated employee details.

    Raises:
        HTTPException: If required fields are missing or an error occurs.
    """
    government_id = attach_data.government_id

    # If government_id is not provided, resolve it using employer_name
    if not government_id:
        if not attach_data.employer_name:
            raise HTTPException(
                status_code=400,
                detail="Government_id must be provided"
            )
    # Attach the employee to the employer
    updated_employee, error = attach_employee_to_employer(attach_data.personal_id, government_id)

    if error:
        raise HTTPException(
            status_code=404,
            detail=error
        )

    return {"message": "Employee attached successfully", "employee": updated_employee}
