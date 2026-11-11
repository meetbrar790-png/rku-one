
import logging
from contextlib import asynccontextmanager

from psycopg.errors import UniqueViolation
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from registration import register_user, verify_login, setup_database
from mail_store import setup_mail, deliver, deliver_many, mailbox
from mail_auth import issue_token, authenticated_id
from profiles import setup_profiles, get_profile, save_profile
from contacts import setup_contacts, list_contacts, save_contact, delete_contact
from attachment_store import setup_attachment_table, setup_message_attachments, save_attachment, get_accessible_attachment
from private_attachments import upload_private, download_private, validate_attachment, MAX_BYTES, StorageError

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.warning("RKU ONE startup: initializing account tables")
    setup_database()
    logging.warning("RKU ONE startup: initializing mail tables")
    setup_mail()
    logging.warning("RKU ONE startup: initializing profile tables")
    setup_profiles()
    logging.warning("RKU ONE startup: initializing contacts tables")
    setup_contacts()
    setup_attachment_table()
    setup_message_attachments()
    logging.warning("RKU ONE startup: database initialization complete")
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
    attachment_id: int | None = None

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
        count = deliver_many(sender, recipients, message.subject.strip(), message.body.strip()) if message.attachment_id is None else deliver_many(sender, recipients, message.subject.strip(), message.body.strip(), message.attachment_id)
    except ValueError as exc:
        if str(exc).startswith("Sending limit reached"):
            raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "60"})
        raise HTTPException(400, str(exc))
    return {"success": True, "delivered": count}

@app.get("/mail/inbox")
def inbox(before: int | None = None, authorization: str | None = Header(default=None)):
    if before is not None and before < 1:
        raise HTTPException(400, "Invalid mail cursor")
    return mailbox(authenticated_id(authorization), before=before)

@app.get("/mail/sent")
def sent(before: int | None = None, authorization: str | None = Header(default=None)):
    if before is not None and before < 1:
        raise HTTPException(400, "Invalid mail cursor")
    return mailbox(authenticated_id(authorization), True, before=before)

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


class ContactData(BaseModel):
    rku_id: int
    nickname: str = ""


@app.get("/contacts")
def contacts_list(authorization: str | None = Header(default=None)):
    return list_contacts(authenticated_id(authorization))


@app.post("/contacts")
def contacts_save(contact: ContactData, authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    try:
        return save_contact(owner, contact.rku_id, contact.nickname)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/contacts/remove")
def contacts_remove(contact: ContactData, authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    if contact.rku_id < 1:
        raise HTTPException(400, "Invalid RKU ID")
    return delete_contact(owner, contact.rku_id)

# Draft attachment endpoints. Objects remain private and accessible only to their owner.
@app.post("/attachments/upload")
async def attachment_upload(file: UploadFile = File(...), authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    mime = file.content_type or ""
    filename = (file.filename or "attachment").replace("\\", "/").split("/")[-1].strip()
    if not filename or len(filename) > 150 or any(ord(c) < 32 for c in filename):
        raise HTTPException(400, "Invalid attachment filename")
    try:
        content = await file.read(MAX_BYTES + 1)
        validate_attachment(content, mime)
        path = upload_private(owner, content, mime)
        attachment_id = save_attachment(owner, path, mime, filename, len(content))
        return {"id": attachment_id, "filename": filename, "size": len(content), "mime": mime}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except StorageError:
        raise HTTPException(503, "Private attachment storage unavailable")
    finally:
        await file.close()


@app.get("/attachments/{attachment_id}")
def attachment_download(attachment_id: int, authorization: str | None = Header(default=None)):
    owner = authenticated_id(authorization)
    if attachment_id < 1:
        raise HTTPException(404, "Attachment not found")
    row = get_accessible_attachment(owner, attachment_id)
    if not row:
        raise HTTPException(404, "Attachment not found")
    path, mime, filename = row
    try:
        content = download_private(path)
    except StorageError:
        raise HTTPException(503, "Private attachment storage unavailable")
    from urllib.parse import quote
    return Response(content=content, media_type=mime, headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(filename, safe=""),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })
