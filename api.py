
import logging
from contextlib import asynccontextmanager

from psycopg.errors import UniqueViolation
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from registration import register_user, verify_login, setup_database
from mail_store import setup_mail, deliver, mailbox
from mail_auth import issue_token, authenticated_id

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    setup_mail()
    yield


app = FastAPI(title="RKU ONE API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rku-one.onrender.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class MailData(BaseModel):
    to: int
    subject: str
    body: str

class UserData(BaseModel):
    email: EmailStr
    password: str


@app.get("/")
def home():
    return {"message": "RKU ONE API Ready"}


@app.post("/register")
def register(user: UserData):
    try:
        result = register_user(user.email, user.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered. Please log in.")
    
    except Exception:
        logging.exception("Registration failed")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

@app.post("/login")
def login(user: UserData):
    try:
        result = verify_login(user.email, user.password)
    except Exception:
        logging.exception("Login failed")
        raise HTTPException(status_code=500, detail="Login temporarily unavailable")

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {**result, "token": issue_token(result["rku_id"])}

@app.post("/mail/send")
def send_message(message: MailData, authorization: str | None = Header(default=None)):
    sender = authenticated_id(authorization)
    if message.to < 1 or not message.subject.strip() or not message.body.strip() or len(message.subject)>200 or len(message.body)>10000:
        raise HTTPException(400, "Please enter a valid recipient, subject and message")
    try:
        deliver(sender, message.to, message.subject.strip(), message.body.strip())
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return {"success": True}

@app.get("/mail/inbox")
def inbox(authorization: str | None = Header(default=None)):
    return mailbox(authenticated_id(authorization))

@app.get("/mail/sent")
def sent(authorization: str | None = Header(default=None)):
    return mailbox(authenticated_id(authorization), True)
