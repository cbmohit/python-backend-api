from fastapi import FastAPI, Header, HTTPException, status, Request
from datetime import datetime, timedelta, timezone
import jwt
from typing import Union
import uvicorn

ACCESS_TOKEN_EXPIRY_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = "123!@£qwerty"
API_KEY = "test123"

app = FastAPI()


class Item():
    id: str
    password: str

@app.get("/")
def read_root():
    return {"msg":"This is message from root! Hello World"}


@app.post("/register")
def create_user(items : dict):
    print(items)
    return {'username':items['id'], 'pass':items['password']}


@app.post("/token")
def create_token(request : Request, x_api_key = Header(None)):
    #x_api_key = request.headers.get('x-api-key')
    print(f"Printing key : {x_api_key}")
    if(x_api_key != API_KEY):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid API Key"
        )
    token = generateToken()
    return {"access_token" : token, "token_type":"bearer"}

def generateToken():
    print("Token Generated")
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
    payload = {
        "exp":expire,
        "sub":"Ios App"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

@app.post("/validate")
def validate_token(authorization = Header(None)):
    print("Token is :"+authorization)
    token_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired Token"
    )
    try:
        payload = jwt.decode(authorization, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        subject:str = payload.get("sub")
        if subject is None:
            raise token_exception
        else:
            return {"msg":"Token Successfully validated"}
    except:
        print('Exception Occurred')
        raise token_exception


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port= 8080, log_level="info")