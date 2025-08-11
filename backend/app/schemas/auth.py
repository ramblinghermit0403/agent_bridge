from pydantic import BaseModel

class login(BaseModel):
    email:str
    password:str