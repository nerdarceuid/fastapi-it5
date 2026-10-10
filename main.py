from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import initialize_database
from app.exceptions import ConflictError, NotFoundError
from app.routers import borrowers, categories, equipment

app = FastAPI(title="Lab Equipment Borrowing API")

app.include_router(categories.router)
app.include_router(equipment.router)
app.include_router(borrowers.router)

@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, error: NotFoundError):

    return JSONResponse(status_code=404, content={"detail": str(error)})

@app.exception_handler(ConflictError)
async def handle_conflict(request: Request, error: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})

@app.get("/")
def read_root():
    return {"message": "The API is working look at docs"}

initialize_database()