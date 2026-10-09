from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Lab Equipment Borrowing API")


@app.get("/")
def read_root():
    return {"message": "The API is working look at docs"}
