from fastapi import FastAPI
from app.api.v1 import test_endpoints

app = FastAPI(title="Agent - AI Call Receptionist Platform")

app.include_router(test_endpoints.router)

@app.get("/")
def health_check():
    return {"status": "ok"}