from ..database import database
from sqlalchemy import Integer,Column,String,BigInteger,TIMESTAMP,func,Boolean, ForeignKey,DateTime,UniqueConstraint,JSON
from datetime import datetime
from sqlalchemy import Index, text


# user model

class User(database.Base):
    __tablename__="Users"
    id=Column(String, primary_key=True)
    username=Column(String)
    email=Column(String)
    password_hash=Column(String)


