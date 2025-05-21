from fastapi import FastAPI
from routes.match import router as match_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to ResuMatch API"}

app.include_router(match_router, prefix="/api")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)