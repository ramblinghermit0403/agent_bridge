from fastapi import Depends, HTTPException, status, APIRouter
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from ..schemas import JWTtoken_schema, user
from ..models import User
from ..database import database
from sqlalchemy.future import select
router = APIRouter()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        
        token_data = JWTtoken_schema.TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    
    result = await db.execute(
        select(User.User).filter(User.User.email == email)
    )
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    return user

@router.get("/user")
async def get_user_info(current_user: User.User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.username
        # Add more fields as needed
    }
