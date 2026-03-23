from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from connections import Base
from datetime import datetime


# ------------------------
# User Table
# ------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)

    # Relationships
    issues = relationship("Issue", back_populates="user")

    # appointments where this user is the client
    user_appointments = relationship(
        "Appointment",
        foreign_keys="Appointment.user_id",
        back_populates="user"
    )

    # appointments where this user is the counselor
    counselor_appointments = relationship(
        "Appointment",
        foreign_keys="Appointment.counselor_id",
        back_populates="counselor"
    )

    chat_messages = relationship("ChatMessage", back_populates="user")


# ------------------------
# Issue Table
# ------------------------
class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="Pending")
    counselor_reply = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    date_posted = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="issues")


# ------------------------
# Appointment Table
# ------------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    status = Column(String(50), default="Pending")
    payment_method = Column(String(50), nullable=True)
    meet_link = Column(String(255), nullable=True)

    # Relationships
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_appointments"
    )

    counselor = relationship(
        "User",
        foreign_keys=[counselor_id],
        back_populates="counselor_appointments"
    )


# ------------------------
# Chat Message Table
# ------------------------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sender = Column(String(10))  # user or ai
    text = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")