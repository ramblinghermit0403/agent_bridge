from pydantic import BaseModel
from pydantic import BaseModel
from typing import List, Optional



class newuser(BaseModel):
    username:str
    email:str
    password:str

# login user model

class LoginUser(BaseModel):
    username:str
    password:str



