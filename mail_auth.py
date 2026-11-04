import os, hmac, hashlib, base64, json, time
from fastapi import HTTPException

def issue_token(rku_id):
    payload = base64.urlsafe_b64encode(json.dumps({"id":rku_id,"exp":int(time.time())+86400}).encode()).decode().rstrip("=")
    signature = hmac.new(os.environ["RKU_SESSION_SECRET"].encode(),payload.encode(),hashlib.sha256).hexdigest()
    return payload+"."+signature

def authenticated_id(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401,"Please log in")
    if len(authorization) > 4096:
        raise HTTPException(401,"Invalid session token")
    try:
        payload, signature = authorization[7:].split(".",1)
        expected = hmac.new(os.environ["RKU_SESSION_SECRET"].encode(),payload.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,expected):
            raise ValueError()
        data=json.loads(base64.urlsafe_b64decode(payload+"="*(-len(payload)%4)))
        if (type(data.get("exp")) is not int or data["exp"] <= time.time() or type(data.get("id")) is not int or data["id"] < 1):
            raise ValueError()
        return data["id"]
    except (ValueError,KeyError,TypeError,OverflowError,IndexError,UnicodeDecodeError,json.JSONDecodeError):
        raise HTTPException(401,"Session expired. Please log in again")
