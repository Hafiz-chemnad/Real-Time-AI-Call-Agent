from fastapi import FastAPI

app = FastAPI(title="Agent - AI Call Receptionist Platform")

@app.get("/")
def health_check():
    return {"status": "ok"}