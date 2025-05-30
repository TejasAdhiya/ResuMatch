from fastapi import FastAPI
from routes.match import router as match_router
from routes.bulk_analysis import router as bulk_analysis_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to ResuMatch API"}

app.include_router(match_router, prefix="/api")
app.include_router(bulk_analysis_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
