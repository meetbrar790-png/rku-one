"""Isolated VIP interest-request test app; NOT imported by production api.py.

Requests are held only in an in-memory SQLite database and disappear on restart.
No number reservation, allocation, payment, or production database access.
"""
import sqlite3
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from mail_auth import authenticated_id
from vip_interest_test_store import record_test_interest
from vip_interest_test_limiter import TestOnlyInterestLimiter

app = FastAPI(title="RKU ONE VIP Interest Staging Prototype")
db = sqlite3.connect(":memory:", check_same_thread=False)
limiter = TestOnlyInterestLimiter(max_requests=5, window_seconds=60)


class InterestInput(BaseModel):
    numeric_id: str = Field(min_length=1, max_length=18)
    request_key: str = Field(min_length=8, max_length=80)


@app.post("/staging/vip/interest")
def submit_staging_interest(data: InterestInput, authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    if not limiter.allow(owner):
        raise HTTPException(status_code=429, detail="Too many staging requests; try later")
    try:
        with db:
            result = record_test_interest(db, data.numeric_id, owner, data.request_key)
        return {**result, "notice": "Test request received only. Number NOT reserved. No payment."}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
