from fastapi import FastAPI, Header, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
import jwt
from typing import Union
import uvicorn
from openai import OpenAI, OpenAIError
import json
from dotenv import load_dotenv
import gunicorn
import os

ACCESS_TOKEN_EXPIRY_MINUTES = 30
ALGORITHM = "HS256"

app = FastAPI()

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")


@app.get("/")
def read_root():
    return {"msg":"This is message from root! Hello World"}


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

def token_validation(token):
    token_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired Token"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject:str = payload.get("sub")
        if subject is None:
            raise token_exception
        else:
            return True
    except:
        raise token_exception



@app.post("/moderation")
def moderation(request = Body(None), authorization = Header(None)):
    token_validation(authorization)
    if request:
        response = openAI_moderation(request)
        return response
    else:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Bad Request"
        )

def openAI_moderation(request):
    client = OpenAI(api_key=openai_key)
    try:
        moderation = client.moderations.create(
            input = request['input']
        )
    except OpenAIError as e:
        return JSONResponse(
            status_code=500,
            content=e.body
        )

    return moderation

def openAI_completion(request):
    client = OpenAI(api_key=openai_key)
    try:
        completion = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt= request['input'],
            max_tokens=7,
            temperature=0
        )
    except OpenAIError as e:
        return JSONResponse(
            status_code=500,
            content=e.body
        )

    return completion


@app.post("/completion")
def completion(request = Body(None), authorization = Header(None)):
    token_validation(authorization)
    if request:
        modResponse = openAI_moderation(request)

        if(modResponse.results[0].flagged == True):
            return JSONResponse(
                status_code= 404,
                content={"detail" : "Moderation Response Flagged True"}
            )

        response = openAI_completion(request)
        return response
    else:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Bad Request"
        )
    

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port= int(8080))