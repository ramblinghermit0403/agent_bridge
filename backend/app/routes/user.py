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
from fastapi.security import OAuth2PasswordBearer
import jwt
from ..auth import oauth2 

from datetime import datetime, timedelta
import uuid


router=APIRouter(tags=['User'])
from datetime import datetime, timezone




# Optional auth scheme
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

@router.post('/register')
async def new_user(
    request: Request,
    body: user.newuser,
    token: str = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(database.get_db)):
    
    current_guest_user = None
    if token:
        try:
            payload = jwt.decode(token, oauth2.SECRET_KEY, algorithms=[oauth2.ALGORITHM])
            email: str = payload.get("sub")
            if email:
                # Find the user
                res = await db.execute(select(User.User).filter(User.User.email == email))
                found_user = res.scalars().first()
                if found_user and found_user.is_guest:
                    current_guest_user = found_user
        except Exception as e:
            # Invalid token or other error, ignore and proceed as fresh signup
            print(f"Guest token check failed: {e}")
            pass

    # If we found a valid guest user, update them instead of creating new
    if current_guest_user:
        # Check if the NEW email is already taken by SOMEONE ELSE (not the guest)
        # Note: Guest email is dummy, so it won't match body.email likely.
        
        # Check if real email already exists
        result = await db.execute(
            select(User.User).filter(User.User.email == body.email)
        )
        existing_real_user = result.scalars().first()
        if existing_real_user:
             raise HTTPException(
                status_code=400,
                detail="Account with this email already exists"
            )
            
        # Update Guest
        current_guest_user.username = body.username
        current_guest_user.email = body.email
        current_guest_user.password_hash = hashing.Hash.bcrypt(body.password)
        current_guest_user.is_guest = False
        
        db.add(current_guest_user)
        await db.commit()
        await db.refresh(current_guest_user)
        
        return {"success": True, "message": "Guest account converted to full account successfully"}

    
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