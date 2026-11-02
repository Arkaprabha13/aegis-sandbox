from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import db

app = FastAPI()
db.init()


class TransferRequest(BaseModel):
    amount: float
    to_user: str


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/state")
async def state():
    return db.get_all()


@app.post("/api/internal/transfer")
async def transfer(req: TransferRequest):
    if not db.transfer(req.amount, req.to_user):
        raise HTTPException(status_code=400, detail="Transfer rejected")
    return {"status": "success", "tx_id": "mock_001"}
