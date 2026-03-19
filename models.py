from sqlalchemy import Column, Integer, String
from connections import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    
   



 