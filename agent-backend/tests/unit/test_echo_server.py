# test_echo_server.py
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/echo")
async def echo(request: Request):
    body = await request.json()
    print(f"📥 Echo server received: {body}")
    return {"received": body, "status": "booked", "appointment_id": "test-12345"}