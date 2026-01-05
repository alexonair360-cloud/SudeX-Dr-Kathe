from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import get_database
from models import UserCreate, UserResponse, UserInDB, Token
from auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta, datetime
import os
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

class GoogleAuthRequest(BaseModel):
    token: str

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "640078566704-rgvkkfilteg23ihnecfu1f95i24i4cck.apps.googleusercontent.com")

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = await get_database()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(
        **user.dict(exclude={"password"}),
        hashed_password=hashed_password
    )
    
    result = await db.users.insert_one(user_in_db.dict(by_alias=True))
    user_in_db.id = result.inserted_id
    
    return UserResponse(id=str(result.inserted_id), **user.dict())

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = await get_database()
    user = await db.users.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest):
    try:
        # Verify the ID token
        idinfo = id_token.verify_oauth2_token(request.token, requests.Request(), GOOGLE_CLIENT_ID)

        # ID token is valid. Get user's Google info
        email = idinfo['email']
        full_name = idinfo.get('name', '')
        
        db = await get_database()
        
        # Check if user exists
        user = await db.users.find_one({"email": email})
        
        if not user:
            # Create user if not exists
            user_in_db = UserInDB(
                email=email,
                full_name=full_name,
                hashed_password="", # No password for Google users
                created_at=datetime.utcnow()
            )
            result = await db.users.insert_one(user_in_db.dict(by_alias=True))
            user = await db.users.find_one({"_id": result.inserted_id})

        access_token = create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
