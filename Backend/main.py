from fastapi import FastAPI
from routes.match import router as match_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to ResuMatch API"}

app.include_router(match_router, prefix="/api")
