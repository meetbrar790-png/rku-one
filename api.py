
import logging
from contextlib import asynccontextmanager

from psycopg.errors import UniqueViolation
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from registration import register_user, verify_login, setup_database
from mail_store import setup_mail, deliver, deliver_many, mailbox
from mail_auth import issue_token, authenticated_id
from profiles import setup_profiles, get_profile, save_profile

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    setup_mail()
    setup_profiles()
    yield


app = FastAPI(title="RKU ONE API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rku-one.onrender.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


class MailData(BaseModel):
    to: int | list[int]
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
    if not message.subject.strip() or not message.body.strip() or len(message.subject)>200 or len(message.body)>10000:
        raise HTTPException(400, "Please enter a valid recipient, subject and message")
    try:
        recipients = message.to if isinstance(message.to, list) else [message.to]
        count = deliver_many(sender, recipients, message.subject.strip(), message.body.strip())
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"success": True, "delivered": count}

@app.get("/mail/inbox")
def inbox(authorization: str | None = Header(default=None)):
    return mailbox(authenticated_id(authorization))

@app.get("/mail/sent")
def sent(authorization: str | None = Header(default=None)):
    return mailbox(authenticated_id(authorization), True)

class ProfileData(BaseModel):
    name: str = ""
    company: str = ""
    logo_url: str = ""
    public: bool = False

@app.get("/profile/me")
def my_profile(authorization: str | None = Header(default=None)):
    return get_profile(authenticated_id(authorization), True)

@app.post("/profile/me")
def update_profile(profile: ProfileData, authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    name, company, logo = profile.name.strip(), profile.company.strip(), profile.logo_url.strip()
    if len(name)>80 or len(company)>120 or len(logo)>500:
        raise HTTPException(400,"Profile fields are too long")
    if logo and (not logo.startswith("https://") or any(x in logo for x in ["<",">"," ","\\"])):
        raise HTTPException(400,"Logo must be an HTTPS image URL")
    return save_profile(owner,name,company,logo,profile.public)

@app.get("/profile/{rku_id}")
def public_profile(rku_id: int):
    if rku_id<1:
        raise HTTPException(400,"Invalid RKU ID")
    return get_profile(rku_id)
