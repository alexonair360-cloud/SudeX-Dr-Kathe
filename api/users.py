from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import get_database
from models import UserCreate, UserResponse, UserInDB, Token
from auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta, datetime
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
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
    email = None
    full_name = ""
    
    try:
        # 1. Try to verify as an ID Token (JWT)
        try:
            idinfo = id_token.verify_oauth2_token(request.token, google_requests.Request(), GOOGLE_CLIENT_ID)
            email = idinfo['email']
            full_name = idinfo.get('name', '')
        except ValueError:
            # 2. If it's not a valid ID Token, it might be an Access Token (Custom Button Flow)
            # Fetch user info from Google API using the access token
            user_info_response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                params={"access_token": request.token}
            )
            if user_info_response.status_code == 200:
                user_data = user_info_response.json()
                email = user_data.get('email')
                full_name = user_data.get('name', '')
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token (Access Token check failed)"
                )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve email from Google"
            )
            
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
        
    except Exception as e:
        print(f"Google Auth Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(e)}"
        )
