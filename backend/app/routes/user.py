from fastapi import APIRouter,Depends,HTTPException,UploadFile,Request
from ..models import User
from ..schemas import user
from ..database import database
from sqlalchemy.orm import Session
from ..auth import hashing
import secrets   
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
from ..auth.oauth2 import get_current_user
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import hmac
import hashlib
from fastapi import FastAPI, HTTPException, Depends

from datetime import datetime, timedelta
import uuid
import boto3

from datetime import datetime, timezone

from botocore.exceptions import ClientError


router=APIRouter(tags=['User'])
from datetime import datetime, timezone



@router.post('/register')
async def new_user(
    request: Request,
    body: user.newuser,
    db: AsyncSession = Depends(database.get_db)):

    
    # Check for existing user
    result = await db.execute(
        select(User.User).filter(
            (User.User.email == body.email) 
        )
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Account with this email or phone number already exists"
        )
    
    # Create a new user
    api_key = secrets.token_hex(32)
    registeruser = User.User( 
        id=str(uuid.uuid4()),
        username=body.username,
        email=body.email,
        password_hash=hashing.Hash.bcrypt(body.password),  # Decode the hash to store it as a string

    )
    
    db.add(registeruser)
    await db.commit()  # Commit the transaction asynchronously
    await db.refresh(registeruser)  # Refresh the instance asynchronously

    return {"success": True, "message": "Account created successfully"}


from fastapi import Depends
from pydantic import BaseModel
# ... import your existing get_current_user and other dependencies

# A Pydantic model for the data you want to send to the frontend
# Crucially, it does NOT include the password hash.
class UserOut(BaseModel):
    username: str
    email: str

# Your existing get_current_user function remains the same

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get details for the currently logged-in user.
    """
    return current_user