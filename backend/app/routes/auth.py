from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import JWTtoken_schema, user
from ..models import User
from ..database import database
from ..auth.hashing import Hash
from ..auth.oauth2 import get_current_user
from ..auth import JWTtoken
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(tags=["Auth"])

# @router.post("/login")
# def login(request: OAuth2PasswordRequestForm=Depends(), db: Session = Depends(database.get_db)):
#     # Find the user by email
#     user = db.query(User.User).filter(User.User.email == request.username).first()

#     # Check if the user exists
#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid Credentials")
    
#     #user # Verify the password
   
   
#     if not Hash.verify(request.password, user.password_hash):
#         raise HTTPException(status_code=400, detail="Invalid password")
    

#     access_token = JWTtoken.create_access_token(
#         data={"sub": user.email})
   
#     return {"access_token":access_token,"token-type":"bearer"}
    
    # Return user information or a token (depending on your implementation)
    # return {"message": "Login successful", "user": user.password_hash}


# @router.get("/users/me", response_model=user.newuser)
# def read_users_me(current_user: JWTtoken_schema.TokenData = Depends(get_current_user)):
#     return current_user

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()

@router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    # Find the user by email
    result = await db.execute(
        select(User).filter(User.email == request.username)
    )
    user = result.scalars().first()

    # Check if the user exists
    if not user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    # Verify the password
    if not Hash.verify(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid password")

    access_token = JWTtoken.create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/guest")
async def login_guest(db: AsyncSession = Depends(database.get_db)):
    import uuid
    # Create unique guest identity
    guest_uuid = str(uuid.uuid4())
    guest_email = f"guest_{guest_uuid}@brainvault.app"
    
    # Create guest user
    new_guest = User(
        id=guest_uuid,
        username="Guest User",
        email=guest_email,
        password_hash=None, # No password
        is_guest=True
    )
    
    db.add(new_guest)
    await db.commit()
    await db.refresh(new_guest)
    
    # Generate token (Guest tokens valid for 30 days)
    from datetime import timedelta
    access_token = JWTtoken.create_access_token(
        data={"sub": guest_email},
        expires_delta=timedelta(days=30) 
    )
    
    return {"access_token": access_token, "token_type": "bearer", "is_guest": True, "user": {"email": guest_email, "username": "Guest User"}}
