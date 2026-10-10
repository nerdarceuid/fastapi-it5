from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import initialize_database
from app.exceptions import ConflictError, NotFoundError
from app.routers import borrowers, categories, equipment
from app.routers import borrowers, categories, equipment, loans
app = FastAPI(title="Lab Equipment Borrowing API")

app.include_router(categories.router)
app.include_router(equipment.router)
app.include_router(borrowers.router)
app.include_router(loans.router)


"""
Error handlers

"""
@app.exception_handler(NotFoundError)

async def handle_not_found(request: Request, error: NotFoundError):
    #any error would be back with HTTP Status 404
    return JSONResponse(status_code=404, content={"detail": str(error)})

#same idea for conflicting errors- request is valid but clashes with existing data
@app.exception_handler(ConflictError)
async def handle_conflict(request: Request, error: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.get("/")
def read_root():
    return {"message": "The API is working look at docs"}

#creates the database tables if they do not exists
initialize_database()