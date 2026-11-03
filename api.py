
import logging
from contextlib import asynccontextmanager

from psycopg.errors import UniqueViolation
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from registration import register_user, verify_login, setup_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(title="RKU ONE API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rku-one.onrender.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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

    return result
